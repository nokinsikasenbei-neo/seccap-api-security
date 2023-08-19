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
def get_user_image(user_id, filename):
    response = requests.get(f"{BASE_URL}/user/{user_id}/image")
    
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
        return f"Image saved to {filename}"
    else:
        return response.text

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
    image_url = "https://2.bp.blogspot.com/-Hr4qJ60inkA/WvQHrreg1yI/AAAAAAABL8k/AU10QMNgi54pYyt-i-ttCtDnEK2Ln-m_wCLcBGAs/s800/network_dennou_sekai_man.png"

    # ユーザー画像を登録
    image_result = register_user_image(image_url, token)
    print(f"Image Registration Result: {image_result}")

    # ユーザー画像を取得して保存
    user_image_filename = "user_image.png"
    image_download_result = get_user_image(user_info["id"], user_image_filename)
    print(image_download_result)