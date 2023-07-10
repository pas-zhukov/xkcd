import requests
from pprint import pprint
from img_functions import download_image, get_file_extension
import os

CURRENT_COMIC_API_URL = 'https://xkcd.com/info.0.json'


def main():
    comic_id = 1

    comic_filname, comic_comment = download_xkcd_comic(comic_id)


def download_xkcd_comic(comic_id: int):
    api_url = f'https://xkcd.com/{comic_id}/info.0.json'
    response = requests.get(api_url)
    response.raise_for_status()
    comic = response.json()
    comic_img_url = comic['img']
    filename = get_file_extension(comic_img_url)[0]
    download_image(comic_img_url, filename)
    return filename, comic['alt']


def post_comic_on_wall(path: str,
                       comic_comment: str,
                       vk_access_token: str,
                       group_id: int,
                       api_version: str = '5.131'):
    #  Getting upload URL.
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
    upload_url = get_link_response.json()['response']['upload_url']

    #  Sending file to server.
    with open(path, 'rb') as file:
        sending_params = {
            'photo': file
        }
        sending_response = requests.post(upload_url, files=sending_params)
        sending_response.raise_for_status()
        save_params = sending_response.json()

    #  Saving image on server.
    save_img_api_url = 'https://api.vk.com/method/photos.saveWallPhoto'
    save_params.update({
        'v': api_version,
        'group_id': 221535503
    })
    save_img_response = requests.post(save_img_api_url, params=save_params, headers=auth_header)
    save_img_response.raise_for_status()
    saved_img_metadata = save_img_response.json()

    #  Posting image on the group wall.
    post_on_wall_api_url = 'https://api.vk.com/method/wall.post'
    post_params = {
        'message': comic_comment,
        'attachments': f'photo{saved_img_metadata["response"][0]["owner_id"]}_{saved_img_metadata["response"][0]["id"]}',
        'from_group': 1,
        'owner_id': -221535503
    }
    post_params.update({
        'v': api_version,
        'group_id': 221535503
    })
    post_response = requests.post(post_on_wall_api_url, params=post_params, headers=auth_header)
    post_response.raise_for_status()
    return post_response.json()


def check_for_error(response: requests.Response):
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