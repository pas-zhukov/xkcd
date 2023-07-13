from argparse import ArgumentParser
import os
import random

from dotenv import load_dotenv
import requests

from img_functions import download_image, get_file_extension


CURRENT_COMIC_API_URL = 'https://xkcd.com/info.0.json'


def main():
    load_dotenv()
    arg_parser = ArgumentParser(
        description="This program allows to post xkcd comics in your VK group."
    )
    arg_parser.add_argument(
        "-id",
        "--comic_id",
        help="ID of comic to post. Default is random.",
        default=get_random_comic_id(),
        type=int
    )
    args = arg_parser.parse_args()

    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')
    try:
        comic_filname, comic_comment = download_xkcd_comic(args.comic_id)
        post_comic_on_wall(comic_filname,
                           comic_comment,
                           vk_access_token,
                           vk_group_id)
    finally:
        os.remove(comic_filname)


def download_xkcd_comic(comic_id: int):
    """
    Downloads xkcd comic.

    Downloads an xkcd comic image and its corresponding
    alt text from the xkcd API, using a given comic ID.
    :param comic_id:  ID of the xkcd comic to be downloaded
    :return: filename of the downloaded image, alt text of the downloaded comic
    """
    api_url = f'https://xkcd.com/{comic_id}/info.0.json'
    response = requests.get(api_url)
    response.raise_for_status()
    comic = response.json()
    comic_img_url = comic['img']
    filename = get_file_extension(comic_img_url)[0]
    download_image(comic_img_url, filename)
    return filename, comic['alt']


def get_upload_url(vk_access_token: str,
                   group_id: int or str,
                   api_version: str) -> str:
    """
    Obtains upload URL.

    Obtains the upload URL for a photo that will
    be posted on a VK group wall.
    :param vk_access_token: access token for VK API
    :param group_id: ID of the VK group
    :param api_version: version of VK API to be used
    :return: URL where the photo should be uploaded
    """
    get_upload_link_api_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    auth_header = {
        'Authorization': f'Bearer {vk_access_token}'
    }
    get_link_params = {
        'v': api_version,
        'group_id': group_id
    }

    get_link_response = requests.get(get_upload_link_api_url,
                                     headers=auth_header,
                                     params=get_link_params)
    get_link_response.raise_for_status()
    raise_if_vk_error(get_link_response)
    upload_url = get_link_response.json()['response']['upload_url']
    return upload_url


def send_file_to_server(path: str,
                        upload_url: str) -> dict:
    """
    Sends file to server.

    Sends a file to a server using a given upload URL and
    return the parameters required to save the file on the server.
    :param path: path of the file to be sent
    :param upload_url: URL of the server to which the file will be sent
    :return: parameters required to save the file on the server
    """
    with open(path, 'rb') as file:
        sending_params = {
            'photo': file
        }
        sending_response = requests.post(upload_url, files=sending_params)
    sending_response.raise_for_status()
    raise_if_vk_error(sending_response)
    save_params = sending_response.json()
    return save_params


def save_image_on_server(server_save_param: int,
                         photo_save_param: str,
                         hash_save_param: str,
                         vk_access_token: str,
                         group_id: int or str,
                         api_version: str) -> dict:
    """
    Saves uploaded photo on server.

    Save an image on the VK server using the VK API method
    'photos.saveWallPhoto' and return the metadata of the saved image.

    :param hash_save_param: uploaded file hash
    :param photo_save_param: photo params (links and etc.)
    :param server_save_param: server num save param
    :param vk_access_token: access token for the VK API
    :param group_id: ID of the VK group
    :param api_version: version of the VK API to be used
    :return: metadata of the saved image
    """
    save_img_api_url = 'https://api.vk.com/method/photos.saveWallPhoto'
    save_params = {
        'v': api_version,
        'group_id': group_id,
        'server': server_save_param,
        'photo': photo_save_param,
        'hash': hash_save_param
    }
    auth_header = {
        'Authorization': f'Bearer {vk_access_token}'
    }

    save_img_response = requests.post(save_img_api_url,
                                      params=save_params,
                                      headers=auth_header)
    save_img_response.raise_for_status()
    raise_if_vk_error(save_img_response)
    saved_img_metadata = save_img_response.json()
    return saved_img_metadata


def _post_on_wall(img_metadata: dict,
                  comic_comment: str,
                  vk_access_token: str,
                  group_id: int or str,
                  api_version: str) -> dict:
    """
    Posts photo. On the wall.

    :param img_metadata: metadata of the image to be posted
    :param comic_comment: comment to be posted along with the image
    :param vk_access_token: access token for VK API
    :param group_id:  ID of the VK group
    :param api_version: version of VK API to be used
    :return: response of the post request
    """
    post_on_wall_api_url = 'https://api.vk.com/method/wall.post'
    post_params = {
        'message': comic_comment,
        'attachments': f'photo{img_metadata["response"][0]["owner_id"]}_{img_metadata["response"][0]["id"]}',
        'from_group': 1,
        'owner_id': f'-{group_id}'
    }
    post_params.update({
        'v': api_version,
        'group_id': group_id
    })
    auth_header = {
        'Authorization': f'Bearer {vk_access_token}'
    }

    post_response = requests.post(post_on_wall_api_url,
                                  params=post_params,
                                  headers=auth_header)
    post_response.raise_for_status()
    raise_if_vk_error(post_response)
    return post_response.json()


def post_comic_on_wall(path: str,
                       comic_comment: str,
                       vk_access_token: str,
                       group_id: int or str,
                       api_version: str = '5.131') -> dict:
    """
    Posts photo on the VK group wall.

    :param path: path of the xkcd comic image to be posted
    :param comic_comment: comment to be posted along with the image
    :param vk_access_token: access token for VK API
    :param group_id: ID of the VK group
    :param api_version: version of VK API to be used
    :return: response of the post request
    """
    upload_url = get_upload_url(vk_access_token,
                                group_id,
                                api_version=api_version)
    save_params = send_file_to_server(path,
                                      upload_url)
    saved_img_metadata = save_image_on_server(save_params['server'],
                                              save_params['photo'],
                                              save_params['hash'],
                                              vk_access_token,
                                              group_id,
                                              api_version)
    vk_post_code = _post_on_wall(saved_img_metadata,
                                 comic_comment,
                                 vk_access_token,
                                 group_id,
                                 api_version)
    return vk_post_code


def get_random_comic_id() -> int:
    """
    Gives you random comic ID.

    Generate a random comic ID within the range
    of the first and the latest comic ID
    available on the xkcd website.
    :return: ID of a comic
    """
    response = requests.get(CURRENT_COMIC_API_URL)
    response.raise_for_status()
    last_comic_id = response.json()['num']
    return random.randint(1, last_comic_id)


def raise_if_vk_error(response: requests.Response):
    """
    Checks if VK response has no errors.

    Raises a custom VKError exception if the VK API
    response contains an error message
    :param response: requests.Response object
    :return: None
    """
    response = response.json()
    try:
        raise VKError(response['error']['error_msg'])
    except KeyError:
        pass


class VKError(requests.HTTPError):
    """

    Custom exception, that handles errors
    from VK API response.
    """
    def __init__(self, message: str = "Error in VK response."):
        super().__init__(message)


if __name__ == '__main__':
    main()
