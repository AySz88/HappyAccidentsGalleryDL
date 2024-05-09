# HappyAccidents Gallery Downloader

This Python project saves your (own) personal images from Happy Accidents, along with prompts and metadata, before it is scheduled to shut down by or on 2024-05-09.

Due to time sensitivity, it strives to preserve data such that your activity and the gallery browsing experience could be reconstructed. However, it does not actually reconstruct such at the moment.

The script is not currently tested beyond the author's use case, and if you encounter any issues, assistance with resolving them would be appreciated.

## Prerequisiates
- Currently tested only on Python 3.9
- See `requirements.txt` for Python packages

## Usage
1. Edit `config.ini` as desired, including output directories.
2. Log into Happy Accidents and find your authorization token. For example: In Chrome, open DevTools, go to the Network panel, and type into the filter box something like 'count', to bring up network requests for e.g. `https://easel-fgiw.onrender.com/v1/inferences/count`. Click one, and in the sidebar that appears, under "Headers", under "Request Headers", find "Authorization". The token will be begin with the word "Bearer" followed by a long string - provide that long string, after the "Bearer" part. ([Screenshot](/docs/auth token in devtools.png))
3. Run `src\main.py`.

The gallery listing has been observed to pause a minute or two after every 1000 images listed; this is presumed to be a server-side throttle.

If the process is interrupted or more new images need to be archived, simply run the script again and it should continue sensibly. (That is, unless you are trying to resume a gallery of many thousands of images, in which case you might need to avoid the aforementioned gallery pagination throttle. Edit the code of Gallery in `downloader.py` to start near where you need to resume.)

The images will appear in your specified destination folder (by default, a new folder called 'output' under the working directory from which the script is running).

To browse images, I recommend grouping by filetype and sorting by the file's modified date (which will be set to the image's generation date).

## License

This project is licensed under the [MIT License](LICENSE).
