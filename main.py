import os
from pathlib import Path
from random import randint

import requests
from dotenv import load_dotenv

API_VERSION = 5.131


def save_remote_comic_and_alt(comic_number: int) -> dict:
    url = f'https://xkcd.com/{comic_number}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    comic_meta = response.json()

    img_url = comic_meta['img']
    extension = Path(img_url).suffix
    img_path = Path(str(comic_number)).with_suffix(extension)

    img_response = requests.get(img_url, stream=True)
    img_response.raise_for_status()
    with open(img_path, 'wb') as file:
        for chunk in img_response.iter_content(chunk_size=128):
            file.write(chunk)
    return {
        'file_path': img_path,
        'alt': comic_meta['alt'],
    }


def upload_comic(comic_path: str) -> dict:
    with open(comic_path, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
        uploaded_photo_meta = response.json()
    return save_wall_photo(uploaded_photo_meta)


# This function exists due to the peculiarity of VK API,
# wherein you need to save an uploaded photo to an album
# before you can post it in the group.
def save_wall_photo(uploaded_photo_meta: dict) -> dict:
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    data = {
        'access_token': access_token,
        'photo': uploaded_photo_meta['photo'],
        'server': uploaded_photo_meta['server'],
        'hash': uploaded_photo_meta['hash'],
        'group_id': group_id,
        'v': API_VERSION,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()

    # Checking for errors since all requests to vk return as 200:
    if 'response' in response.json():
        return response.json()['response'][0]
    else:
        raise requests.exceptions.RequestException('The request to VK returned an error.')


def post_comic(uploaded_photo: dict, alt: str) -> dict:
    url = 'https://api.vk.com/method/wall.post'
    data = {
        'access_token': access_token,
        'v': API_VERSION,
        'owner_id': -group_id,
        'from_group': True,
        'message': alt,
        'attachments': f"photo{uploaded_photo['owner_id']}_{uploaded_photo['id']}",
    }
    response = requests.post(url, data=data)
    response.raise_for_status()

    # Checking for errors since all requests to vk return as 200:
    if 'response' in response.json():
        return response.json()
    else:
        raise requests.exceptions.RequestException('The request to VK returned an error.')


def get_upload_server() -> dict:
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'access_token': access_token,
        'v': API_VERSION,
        'group_id': group_id,
    }
    response = requests.get(url, params=params)

    # Checking for errors since all requests to vk return as 200:
    if 'response' in response.json():
        return response.json()
    else:
        raise requests.exceptions.RequestException('The request to VK returned an error.')


def save_random_comic_and_alt() -> dict:
    latest_comic_url = 'https://xkcd.com/info.0.json'
    response = requests.get(latest_comic_url)
    response.raise_for_status()
    current_number = response.json()['num']
    random_number = randint(1, current_number)
    return save_remote_comic_and_alt(random_number)


def save_and_post_random_comic() -> None:
    comic = save_random_comic_and_alt()
    try:
        uploaded_comic = upload_comic(comic['file_path'])
        post_response = post_comic(uploaded_comic, comic['alt'])
    finally:
        os.remove(comic['file_path'])
    if 'response' not in post_response:
        raise requests.exceptions.RequestException('The request to VK returned an error.')


if __name__ == "__main__":
    load_dotenv()
    access_token = os.getenv('ACCESS_TOKEN')
    upload_url = os.getenv('UPLOAD_URL')
    group_id = int(os.getenv('GROUP_ID'))
    save_and_post_random_comic()
    print('A random comic has been posted.')
