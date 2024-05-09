from downloader import Gallery, Downloader, ModelMetadataManager, Cache
from utils import create_directory
import configparser
import logging
import datetime
import os

def main():
    print("Press Ctrl-C to stop at any time.")
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')

    gallery_url = config.get("HappyAccidents", "gallery_url")
    gallery_pagesize = config.getint("HappyAccidents", "gallery_pagesize")
    gallery_startpage = config.getint("HappyAccidents", "gallery_startpage", fallback=0)
    token = config.get("HappyAccidents", "auth_token", fallback=None)
    if not token:
        if os.path.exists("auth_token.txt"):
            with open("auth_token.txt", "r") as file:
                token = file.read().strip()
        else:
            print("Authorization token not found in config.ini or auth_token.txt")
            token = input("Paste it here and press Enter, or Ctrl-C to cancel: ")
    resave_meta = config.getboolean("Output", "resave_metadata", fallback=False)
    destination_folder = config.get("Output", "download_dest")
    create_directory(destination_folder)
    model_cache_dir = config.get("Output", "model_metadata_dest")
    create_directory(model_cache_dir)
    log_dir = config.get("Output", "log_dest")
    create_directory(log_dir)
    log_level = config.get("Logging", "log_level")
    imagekit_param = config.get("Output", "imagekit_param", fallback=None)
    max_backoff = config.getfloat("Network", "max_backoff")
    min_backoff = config.getfloat("Network", "min_backoff")
    request_timeout = config.getfloat("Network", "request_timeout")
    gallery_request_timeout = config.getfloat("Network", "gallery_request_timeout", fallback=request_timeout)

    # Configure logging
    logfile = f"{log_dir}{os.sep}{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    logging.basicConfig(level=logging.getLevelName(log_level), format='%(asctime)s - %(levelname)s - %(message)s', filename=logfile)
    # Also show messages to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(console_handler)

    # Initialize data structures
    gallery = Gallery(
        url=gallery_url,
        authtoken=token,
        page_size=gallery_pagesize,
        start_page=gallery_startpage,
        request_timeout=gallery_request_timeout
    )
    modeldata = ModelMetadataManager(cache=Cache(model_cache_dir))
    downloader = Downloader(
        model_metadata_manager=modeldata,
        max_backoff=max_backoff,
        min_backoff=min_backoff,
        ik_param=imagekit_param,
        resave_metadata=resave_meta,
        request_timeout=request_timeout
    )

    # Start downloading the images from the gallery
    downloader.download_gallery(gallery, destination_folder)

if __name__ == "__main__":
    main()
