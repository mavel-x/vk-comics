import os
from pathlib import Path
from random import randint

import requests
from dotenv import load_dotenv

API_VERSION = 5.131


def save_remote_comic_with_alt(comic_number: int) -> tuple:
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
    return img_path, comic_meta['alt']


def upload_comic(comic_path: str, access_token: str, upload_url: str, group_id: int) -> dict:
    with open(comic_path, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
        uploaded_photo = response.json()
    return save_wall_photo(uploaded_photo, access_token=access_token, group_id=group_id)


# This function exists due to the peculiarity of VK API,
# wherein you need to save an uploaded photo to an album
# before you can post it in the group.
def save_wall_photo(uploaded_photo: dict, access_token: str, group_id: int) -> dict:
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    data = {
        'access_token': access_token,
        'photo': uploaded_photo['photo'],
        'server': uploaded_photo['server'],
        'hash': uploaded_photo['hash'],
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


def post_comic(uploaded_photo: dict, alt: str, access_token: str, group_id: int) -> dict:
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


def get_upload_server(access_token: str, group_id: int) -> dict:
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


def save_random_comic_with_alt() -> tuple:
    latest_comic_url = 'https://xkcd.com/info.0.json'
    response = requests.get(latest_comic_url)
    response.raise_for_status()
    current_comic_number = response.json()['num']
    random_number = randint(1, current_comic_number)
    return save_remote_comic_with_alt(random_number)


def save_and_post_random_comic(access_token: str, upload_url: str, group_id: int) -> None:
    comic_path, comic_alt = save_random_comic_with_alt()
    uploaded_comic = upload_comic(
        comic_path,
        access_token=access_token,
        upload_url=upload_url,
        group_id=group_id,
    )
    try:
        post_response = post_comic(
            uploaded_comic,
            alt=comic_alt,
            access_token=access_token,
            group_id=group_id,
        )
        if 'response' not in post_response:
            raise requests.exceptions.RequestException('The request to VK returned an error.')
    finally:
        os.remove(comic_path)


if __name__ == "__main__":
    load_dotenv()
    vk_access_token = os.getenv('ACCESS_TOKEN')
    vk_upload_url = os.getenv('UPLOAD_URL')
    vk_group_id = int(os.getenv('GROUP_ID'))
    save_and_post_random_comic(
        access_token=vk_access_token,
        upload_url=vk_upload_url,
        group_id=vk_group_id,
    )
    print('A random comic has been posted.')
