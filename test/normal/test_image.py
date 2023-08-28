import requests
import secrets
import string
import shutil
import pytest
import os

# APIのベースURL
BASE_URL = "http://localhost:8000"  # FastAPIのデフォルトのアドレスとポート

def generate_random_string(length: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

# ユーザー登録
def register_user(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/user/register", json=payload)
    return response.json()

# ログイン
def login_user(username, password):
    data = {
        "username": username,
        "password": password,
        "grant_type": "", 
        "scope": "", 
        "client_id": "", 
        "client_secret": ""
    }
    response = requests.post(f"{BASE_URL}/user/login", data=data)
    return response.json()["access_token"]

# ユーザーの画像を登録
def register_user_image(image_url, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"image_url": image_url}
    response = requests.post(f"{BASE_URL}/user/image", headers=headers, json=payload)
    return response.json()

# ユーザーの画像を取得
def get_user_image(token, filename):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user/image", headers=headers)
    
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
        return f"Image saved to {filename}"
    else:
        return response.text

# usernameとpasswordを生成
username = generate_random_string(10)
password = generate_random_string(10)

# テスト用の画像URL
TEST_IMAGE_URL = "https://2.bp.blogspot.com/-Hr4qJ60inkA/WvQHrreg1yI/AAAAAAABL8k/AU10QMNgi54pYyt-i-ttCtDnEK2Ln-m_wCLcBGAs/s800/network_dennou_sekai_man.png"

# ユーザー登録
def test_register_user():
    user_info = register_user(username, password)
    assert 'username' in user_info
    assert user_info['username'] == username

# ログイン
def test_login_user():
    token = login_user(username, password)
    assert isinstance(token, str)
    assert len(token) > 0

# ユーザー画像登録
def test_register_user_image():
    token = login_user(username, password)
    image_result = register_user_image(TEST_IMAGE_URL, token)
    assert 'success' in image_result['detail']

# ユーザー画像取得
def test_get_user_image():
    token = login_user(username, password)
    filename = "test_user_image.png"
    image_download_result = get_user_image(token, filename)
    assert f"Image saved to {filename}" in image_download_result

    # ダウンロードされた画像ファイルを削除
    os.remove(filename)