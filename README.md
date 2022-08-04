# vk-comics

Automatically post random comics to your VK group.

## How to install

### Install the required packages
Python3 should be already installed. 
Use `pip` to install dependencies:
```console
$ python3 -m pip install -r requirements.txt
```
Optionally, you can use [virtualenv](https://docs.python-guide.org/dev/virtualenvs/#lower-level-virtualenv) 
to install the packages inside a virtual environment and not on your entire system. 
In this case you will need to run the script from the virtual environment as well.

### Prerequisites related to vk.com
1. Create a file named `.env` in the project's root directory.
2. [Create a group](https://vk.com/groups?w=groups_create) on vk.com.
3. Save the group's id into `.env` like so: `GROUP_ID=<your_group_id>` 
4. [Create a VK app](https://vk.com/editapp?act=create). Choose "standalone app".
5. Get your app's client id from the app's settings page. Save it.
6. [Get your VK access token](https://vk.com/dev/implicit_flow_user). Save it in `.env` as `ACCESS_TOKEN=<token>`
7. [Get the url of the server](https://vk.com/dev/photos.getWallUploadServer) you will need to upload images to. 
Save it in `.env` as `UPLOAD_URL`.

## How to use
Run the file:
```commandline
$ python3 main.py
```

## Project Goals

The code was written for educational purposes 
as part of an online course for developers at [dvmn.org](https://dvmn.org/).