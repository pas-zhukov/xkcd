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
        post_comic_on_wall(comic_filname, comic_comment, vk_access_token, vk_group_id)
    finally:
        os.remove(comic_filname)


def download_xkcd_comic(comic_id: int):
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

    get_upload_link_api_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    auth_header = {
        'Authorization': f'Bearer {vk_access_token}'
    }
    get_link_params = {
        'v': api_version,
        'group_id': group_id
    }

    get_link_response = requests.get(get_upload_link_api_url, headers=auth_header, params=get_link_params)
    get_link_response.raise_for_status()
    raise_if_vk_error(get_link_response)
    upload_url = get_link_response.json()['response']['upload_url']
    return upload_url


def send_file_to_server(path: str,
                        upload_url: str) -> dict:
    with open(path, 'rb') as file:
        sending_params = {
            'photo': file
        }
        sending_response = requests.post(upload_url, files=sending_params)
    sending_response.raise_for_status()
    raise_if_vk_error(sending_response)
    save_params = sending_response.json()
    return save_params


def save_image_on_server(save_params: dict,
                         group_id: int or str,
                         api_version: str) -> dict:
    save_img_api_url = 'https://api.vk.com/method/photos.saveWallPhoto'
    save_params.update({
        'v': api_version,
        'group_id': group_id
    })
    save_img_response = requests.post(save_img_api_url, params=save_params, headers=auth_header)
    save_img_response.raise_for_status()
    raise_if_vk_error(save_img_response)
    saved_img_metadata = save_img_response.json()
    return saved_img_metadata


def _post_on_wall(img_metadata: dict,
                  comic_comment: str,
                  group_id: int or str,
                  api_version: str) -> dict:
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
    post_response = requests.post(post_on_wall_api_url, params=post_params, headers=auth_header)
    post_response.raise_for_status()
    raise_if_vk_error(post_response)
    return post_response.json()


def post_comic_on_wall(path: str,
                       comic_comment: str,
                       vk_access_token: str,
                       group_id: int or str,
                       api_version: str = '5.131'):
    upload_url = get_upload_url(vk_access_token, group_id, api_version=api_version)
    save_params = send_file_to_server(path, upload_url)
    saved_img_metadata = save_image_on_server(save_params, group_id, api_version)
    vk_post_code = _post_on_wall(saved_img_metadata, comic_comment, group_id, api_version)
    return vk_post_code


def get_random_comic_id() -> int:
    response = requests.get(CURRENT_COMIC_API_URL)
    response.raise_for_status()
    last_comic_id = response.json()['num']
    return random.randint(1, last_comic_id)


def raise_if_vk_error(response: requests.Response):
    response = response.json()
    try:
        raise VKError(response['error']['error_msg'])
    except KeyError:
        pass


class VKError(requests.HTTPError):
    def __init__(self, message: str = "Error in VK response."):
        super().__init__(message)


if __name__ == '__main__':
    main()
