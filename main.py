import os
from dataclasses import dataclass
from pathlib import Path
from random import randint

import requests
from dotenv import load_dotenv

API_VERSION = 5.131


@dataclass
class VKAuthorization:
    access_token: str
    upload_url: str
    group_id: int


def download_comic_with_alt(comic_number: int) -> tuple:
    url = f'https://xkcd.com/{comic_number}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    comic_meta = response.json()

    comic_alt = comic_meta['alt']
    img_url = comic_meta['img']
    extension = Path(img_url).suffix
    img_path = Path(str(comic_number)).with_suffix(extension)

    img_response = requests.get(img_url, stream=True)
    img_response.raise_for_status()
    with open(img_path, 'wb') as file:
        for chunk in img_response.iter_content(chunk_size=128):
            file.write(chunk)
    return img_path, comic_alt


def upload_comic(comic_path: str, credentials: VKAuthorization) -> dict:
    with open(comic_path, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(credentials.upload_url, files=files)
        response.raise_for_status()
        
    # Checking for errors since all requests to vk return as 200:
    if 'error' in response.json():
        raise requests.exceptions.RequestException(f'VK error: {response.json()["error"]["error_msg"]}')

    uploaded_photo = response.json()
    saved_wall_photo = save_wall_photo(uploaded_photo, credentials)
    return saved_wall_photo


# This function exists due to the peculiarity of VK API,
# wherein you need to save an uploaded photo to an album
# before you can post it in the group.
def save_wall_photo(uploaded_photo: dict, credentials: VKAuthorization) -> dict:
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    data = {
        'access_token': credentials.access_token,
        'photo': uploaded_photo['photo'],
        'server': uploaded_photo['server'],
        'hash': uploaded_photo['hash'],
        'group_id': credentials.group_id,
        'v': API_VERSION,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()

    # Checking for errors since all requests to vk return as 200:
    if 'error' in response.json():
        raise requests.exceptions.RequestException(f'VK error: {response.json()["error"]["error_msg"]}')
    
    return response.json()['response'][0]


def post_comic(uploaded_photo: dict, alt: str, credentials: VKAuthorization) -> dict:
    url = 'https://api.vk.com/method/wall.post'
    data = {
        'access_token': credentials.access_token,
        'v': API_VERSION,
        'owner_id': -(credentials.group_id),
        'from_group': True,
        'message': alt,
        'attachments': f"photo{uploaded_photo['owner_id']}_{uploaded_photo['id']}",
    }
    response = requests.post(url, data=data)
    response.raise_for_status()

    # Checking for errors since all requests to vk return as 200:
    if 'error' in response.json():
        raise requests.exceptions.RequestException(f'VK error: {response.json()["error"]["error_msg"]}')
    
    return response.json()
    
    
def get_latest_comic_number():
    latest_comic_url = 'https://xkcd.com/info.0.json'
    response = requests.get(latest_comic_url)
    response.raise_for_status()
    return response.json()['num']


def download_random_comic_with_alt() -> tuple:
    current_comic_number = get_latest_comic_number()
    random_comic_number = randint(1, current_comic_number)
    return download_comic_with_alt(random_comic_number)


def save_and_post_random_comic(credentials: VKAuthorization) -> None:
    comic_path, comic_alt = download_random_comic_with_alt()
    uploaded_comic = upload_comic(comic_path, credentials)
    try:
        post_comic(
            uploaded_comic,
            alt=comic_alt,
            credentials=credentials,
        )
    finally:
        os.remove(comic_path)


if __name__ == "__main__":
    load_dotenv()
    vk_access_token = os.getenv('ACCESS_TOKEN')
    vk_upload_url = os.getenv('UPLOAD_URL')
    vk_group_id = int(os.getenv('GROUP_ID'))
    vk_credentials = VKAuthorization(
        access_token=vk_access_token,
        upload_url=vk_upload_url,
        group_id=vk_group_id
    )
    save_and_post_random_comic(vk_credentials)
    print('A random comic has been posted.')
