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
def get_user_image(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user/image", headers=headers)
    return response.text

def export_post_to_pdf(post_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/post/export/{post_id}", headers=headers, stream=True)
    print(response.status_code)
    if response.status_code == 200:
        with open(f"post_{post_id}.pdf", 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        return f"post_{post_id}.pdf"
    else:
        return response.json()

def create_post(title, content, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": title, "content": content, "is_private": False}
    response = requests.post(f"{BASE_URL}/post/create", headers=headers, json=payload)
    return response.json()

@pytest.fixture(scope="module")
def registered_user():
    username = generate_random_string(10)
    password = generate_random_string(10)
    user_info = register_user(username, password)
    token = login_user(username, password)
    return username, password, user_info, token

def test_user_image_registration_and_download(registered_user):
    _, _, _, token = registered_user

    image_url = "http://localhost:8000/admin/users"
    
    # ユーザー画像を登録
    image_registration_result = register_user_image(image_url, token)
    assert image_registration_result["detail"] == "Image URL updated successfully"
    
    # ユーザー画像を取得
    image_download_result = get_user_image(token)
    assert image_download_result != None

def test_export_post_to_pdf(registered_user):
    username, _, _, token = registered_user

    # For this test, we assume that there's an endpoint to create a post and return its ID.
    res = create_post("Sample Title", "Sample Content", token)
    post_id = res["id"]

    pdf_filename = export_post_to_pdf(post_id, token)

    # Verify if the file is saved successfully
    assert os.path.exists(pdf_filename)

    # Clean up: delete the downloaded PDF
    os.remove(pdf_filename)