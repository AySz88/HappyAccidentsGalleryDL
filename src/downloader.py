from __future__ import annotations
import requests
import os
from datetime import datetime, timezone
import json
import logging
from typing import Dict, Any, Callable
from utils import is_successful_status, Backoff, Cache
import time

class Gallery:
    def __init__(self, url: str, authtoken: str, page_size: int = 30, start_page = 0):
        self.url = url
        self.authtoken = authtoken
        self.curpage = start_page-1 # Zero-indexed; incremented at the start of fetch_next_page
        self.page_size = page_size # Happy Accidents seems to default to 30 items per page
        self.lastResponse = None

    def fetch_next_page(self, backoff:Backoff) -> requests.Response:
        newpage = self.curpage + 1
        headers = {
            'Authorization': f'Bearer {self.authtoken}',
            'Origin': 'https://www.happyaccidents.ai',
            'Referer': 'https://www.happyaccidents.ai/'
        }
        fullurl = f'{self.url}?current_page={newpage}&page_size={self.page_size}&has_images=true'
        logging.info(f"Fetching gallery page {newpage} from {fullurl}...")
        response = retry_fetch(lambda: requests.get(fullurl, headers=clean_headers(headers)), backoff, "Next gallery page")
        self.lastResponse = response
        self.curpage = newpage
        return response

class Image:
    def __init__(self, image_data: Dict, inference_item_data: Dict, model_metadata: Dict|None, destination_dir: str):
        self.url = image_data['url']
        self.image_metadata = image_data
        self.inference_metadata = inference_item_data
        self.model_metadata = model_metadata
        self.dest_dir = destination_dir
        self.img_destination = os.path.join(destination_dir, image_data['id'] + '.png')
        self.img_meta_dest = self.img_destination.replace(".png", "_metadata.json")
        self.inference_dest = os.path.join(destination_dir, inference_item_data['inferenceId'] + '_inference.json')
    
    def save_metadata(self):
        # File system metadata for the image itself:
        # since it's hard to change creation time, use the inference time as "modified" and the image output time as "accessed"
        prompt_time = self.prompt_time()
        image_time = self.output_time()
        os.utime(self.img_destination, (prompt_time, image_time))
        
        # Save the inference item including all 'images' to one file based on the inferenceId
        if os.path.exists(self.inference_dest):
            logging.debug(f"Inference file already exists: {self.inference_dest}")
        else:
            with open(self.inference_dest, 'w') as file:
                json.dump(self.inference_metadata, file)
        os.utime(self.inference_dest, (prompt_time, prompt_time))

        # Save the image metadata with a copy of the inference metadata (excluding 'images') and model metadata
        if os.path.exists(self.img_meta_dest):
            logging.debug(f"Image metadata file already exists: {self.img_meta_dest}")
        else:
            image_metadata_with_inference_and_model = {
                **self.image_metadata,
                "inference_prefetch": {key: self.inference_metadata[key] for key in self.inference_metadata if key != 'images'},
                "model_prefetch": {key: self.model_metadata[key] for key in {"id", "name", "activeVersionId", "author", "externalId", "modelProvider"}} if self.model_metadata is not None else {}
            }
            with open(self.img_meta_dest, 'w') as file:
                json.dump(image_metadata_with_inference_and_model, file)
        os.utime(self.img_meta_dest, (image_time, image_time))

    def prompt_time(self):
        # Annoyingly, the 'createdAt' key does not seem to actually refer to the time the prompt was submitted
        # They are not all the same but they seem to be all on or near 2024 April 4, regardless of the actual prompt time
        # e.g. my most recent 240 have identical 'createdAt' values of "2024-04-04T23:29:15.431843", then change to "2024-04-04T23:29:51.789698"
        # I will just use the output time for now
        return self.output_time()
        #if not 'createdAt' in self.inference_metadata or self.inference_metadata['createdAt'] == "2024-04-04T23:29:15.431843":
        #    return self.output_time()
        #return datetime.fromisoformat(self.inference_metadata['createdAt']).replace(tzinfo=timezone.utc).timestamp()
    
    def output_time(self):
        # Need to remove 'Z' from end of timestamp
        return datetime.fromisoformat(self.image_metadata['createdAt'][:-1]).replace(tzinfo=timezone.utc).timestamp()

class ModelMetadataManager:
    def __init__(self, cache: Cache):
        self.cache = cache

    def fetch_model_metadata(self, model_id: str) -> Dict:
        cached_metadata = self.cache.get(model_id)
        if cached_metadata is not None:
            return cached_metadata
        else:
            headers = {
                'Origin': 'https://www.happyaccidents.ai',
                'Referer': 'https://www.happyaccidents.ai/'
            }
            response = requests.get(f'https://easel-fgiw.onrender.com/v1/models/metadata-items/{model_id}', headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.cache.set(model_id, data)
                return data
            else:
                logging.error(f"Failed to fetch model metadata for {model_id}")
                return {}

# Check whether keys and values can be encoded to 'latin-1' encoding, and keep only those that can
def clean_headers(headers: Dict[str, str]) -> Dict[str, str]:
    cleaned_headers: Dict[str, str] = {}
    for key, value in headers.items():
        try:
            key.encode('latin-1')
            value.encode('latin-1')
            cleaned_headers[key] = value # don't double-encode
        except UnicodeEncodeError:
            logging.warning(f"Skipping header {key}: {value}")
    return cleaned_headers

def retry_fetch(fetch_function: Callable[..., requests.Response], backoff: Backoff, description: str) -> requests.Response:
    while True:
        try:
            start_time = time.time()
            response = fetch_function()
            end_time = time.time()
            download_time = end_time - start_time
            backoff.be_nice(download_time)
            if not is_successful_status(response):
                raise requests.exceptions.HTTPError(response)
            if not response.text:
                logging.warning(f"{description} fetch returned no data.")
            return response
        except requests.exceptions.HTTPError as e:
            backoff.increment()
            status_code = f", status code {e.response.status_code}" if hasattr(e.response, 'status_code') else ''
            logging.warning(f"{description} request failed with HTTP error {e}{status_code}, retrying in {backoff.current} seconds...")
        except requests.exceptions.RequestException as e:
            backoff.increment()
            logging.error(f"{description} request failed with error {e}, retrying in {backoff.current} seconds...")
        time.sleep(backoff.current)

class Downloader:
    def __init__(self, model_metadata_manager: ModelMetadataManager, max_backoff: float = 15, min_backoff : float = 0.1, ik_param: str|None = None):
        self.model_metadata_manager = model_metadata_manager
        self.gallerybackoff = Backoff(maxTime=max_backoff, minTime=min_backoff)
        self.imgbackoff = Backoff(maxTime=max_backoff, minTime=min_backoff)
        self.ik_param = ik_param # NYI

    def download_image(self, image: Image):
        if os.path.exists(image.img_destination):
            logging.debug(f"Image already downloaded: {image.img_destination}")
            # Uncomment to update already downloaded images
            # image.save_metadata()
            return
        else:
            response = retry_fetch(lambda: requests.get(image.url), self.imgbackoff, "Image")
            if is_successful_status(response):
                with open(image.img_destination, 'wb') as file:
                    file.write(response.content)
                # Set filesystem metadata for image
                image.save_metadata()
                logging.info(f"Image downloaded successfully: {image.img_destination}")
                return
            else:
                logging.error(f"Failed to download image from {image.url} with status code {response.status_code}")
                raise requests.exceptions.HTTPError(response)
    
    def download_gallery(self, gallery: Gallery, destination_dir: str):
        self.gallerybackoff.reset()
        while True: # getting more pages
            page_data = gallery.fetch_next_page(self.gallerybackoff).json()
            this_page_imagecount = 0
            for inference_data in page_data['items']:
                for image_data in inference_data['images']:
                    this_page_imagecount += 1
                    if inference_data['inferenceType'] == 'UPSCALING':
                        model_metadata = None
                    else:
                        # also fetch any lora metadata
                        for lora_data in inference_data['inferencePayload']['lora']:
                            self.model_metadata_manager.fetch_model_metadata(lora_data['id'])
                        model_id = inference_data['inferencePayload']['modelId']
                        model_metadata = self.model_metadata_manager.fetch_model_metadata(model_id)
                    image = Image(image_data, inference_data, model_metadata, destination_dir)
                    self.download_image(image)
            
            # Extract pagination metadata
            pagination_metadata = page_data['paginationMetadata']
            if not pagination_metadata['hasNextPage']:
                # total_items = pagination_metadata.get('totalItems') # doesn't seem to populate correctly
                logging.info(f"Reached the end of the gallery. Total gallery pages: {gallery.curpage+1}") # page is 0-indexed
                logging.info(f"Expected total gallery size: {gallery.curpage*gallery.page_size + this_page_imagecount}")
                return
