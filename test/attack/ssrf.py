import requests
import secrets
import string
import shutil

# APIのベースURL
BASE_URL = "http://localhost:8000"  # FastAPIのデフォルトのアドレスとポート

def generate_random_string(length: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

# ユーザー登録
def register_user(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/user/register/", json=payload)
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
    response = requests.post(f"{BASE_URL}/user/login/", data=data)
    return response.json()["access_token"]

# ユーザーの画像を登録
def register_user_image(image_url, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"image_url": image_url}
    response = requests.post(f"{BASE_URL}/user/image", headers=headers, json=payload)
    return response.json()

# ユーザーの画像を取得
def get_user_image(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user/image", headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        return None

if __name__ == "__main__":
    # usernameとpasswordを生成
    username = generate_random_string(10)
    password = generate_random_string(10)

    # ユーザー登録
    user_info = register_user(username, password)
    print(f"Registered User: {user_info}")

    # ログイン
    token = login_user(username, password)
    print(f"Access Token: {token}")

    # 画像URL
    image_url = "http://localhost:8000/admin/users"

    # ユーザー画像を登録
    image_result = register_user_image(image_url, token)
    print(f"Image Registration Result: {image_result}")

    # ユーザー画像を取得して保存
    image_download_result = get_user_image(token)
    print(image_download_result)