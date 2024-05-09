# HappyAccidents Gallery Downloader

This Python project saves your (own) personal images from [Happy Accidents](https://www.happyaccidents.ai/), along with prompts and metadata, before it is scheduled to shut down on 2024-05-09.

Due to time sensitivity, it strives to preserve data such that your activity and the gallery browsing experience could be reconstructed. However, it does not actually reconstruct such at the moment.

The script has not been comprehensively tested. If you encounter [issues](../../issues), assistance with resolving them would be appreciated, especially push requests.

## Prerequisites
- Python 3.9 or similar (reported used on 3.9 through 3.12)
- See `requirements.txt` for Python packages. Currently only `requests`.

## Usage
1. Edit `config.ini` as desired, including output directories.
2. Log into Happy Accidents and find your authorization token (process varies by browser). Save it in `config.ini` or to a new file `auth_token.txt`.
    - For example, using Google Chrome (see [screenshot](/doc/auth%20token%20in%20devtools.png)):
        1. Open DevTools
        2. Go to the Network panel
        3. Type into the filter box something like 'count', to bring up network requests for e.g. `https://easel-fgiw.onrender.com/v1/inferences/count`
        4. Click one of the requests
        5. In the sidebar that appears, under "Headers", under "Request Headers", find "Authorization"
        6. The token will begin with the word "Bearer" followed by a long string. Provide that long string, after the "Bearer" part.
3. In a terminal or command prompt, navigate to the project's root directory.
4. Install the required Python packages by running `pip install -r requirements.txt`.
5. Run the script `python3 src/main.py`. Press `Ctrl-C` at any time to interrupt it.

The images will appear in your specified destination folder (by default, a new folder called 'output' under the working directory from which the script is running).

To browse images, I recommend grouping by filetype and sorting by the file's modified date (which will be set to the image's generation date).

### Notes
The gallery listing has been observed to pause a minute or two after every 1000 images listed; this is presumed to be a server-side throttle.

If the process is interrupted or more new images need to be archived, simply run the script again and it should continue sensibly. (If you need to resume a large gallery of many thousands of images, you might want to set the configuration option `gallery_startpage` to avoid the aforementioned gallery pagination throttle.)

In earlier versions, metadata for certain textual inversion or embedding models weren't saved. To reprocess the metadata for images already downloaded, set the `resave_metadata` option in the configuration file to `true`, and run the script again.

## License

This project is licensed under the [MIT License](LICENSE).
