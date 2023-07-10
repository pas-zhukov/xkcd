import os
from random import shuffle
import pathlib
from urllib.parse import urlparse, unquote
from datetime import datetime
import requests


def download_image(image_url: str,
                   path: str = f"images/image_{datetime.now().strftime('%H%M_%d%m%y')}.jpg",
                   params: dict = None):
    """

    This function downloads an image from a given URL
    and save it to a specified path on the local machine.

    :param image_url: the URL of the image to be downloaded
    :param path: the path where the downloaded image will be saved
    (default is a path with the current date and time in the filename,
    located in the "images/" directory)
    :param params: optional parameters to be passed in the request
    :return: path to the downloaded image
    """
    pathlib.Path(os.path.split(path)[0]).mkdir(parents=True, exist_ok=True)
    response = requests.get(image_url, params=params)
    response.raise_for_status()
    binary_image = response.content
    with open(path, 'bw+') as file:
        file.write(binary_image)
    return path


def get_file_extension(image_url: str) -> tuple[str, str]:
    """

    Returns the filename and extension of a file from a given URL.

    :param image_url: The URL of the file.
    :return: A tuple containing the filename and extension of the file.
    """
    path_only = unquote(urlparse(image_url).path)
    filename = os.path.split(path_only)[1]
    extension = os.path.splitext(path_only)[1]
    return filename, extension

