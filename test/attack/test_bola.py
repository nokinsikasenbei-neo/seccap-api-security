import requests
import secrets
import string
import pytest

BASE_URL = "http://localhost:7000"

def generate_random_string(length: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def register_user(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/user/register", json=payload)
    return response.json()

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

def create_private_post(title, content, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": title, "content": content, "is_private": True}
    response = requests.post(f"{BASE_URL}/post/create", headers=headers, json=payload)
    return response.json()

def get_post_by_id(post_id, token):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/post/{post_id}", headers=headers)
    return response.json()

def get_user_profile_by_id(user_id, token):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/user/profile/{user_id}", headers=headers)
    return response.json()

def update_username(username, token):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.put(f"{BASE_URL}/user/username", headers=headers, json={"new_username": username})
    return response.json()

@pytest.fixture(scope="module")
def registered_user():
    username = "admin"
    password = generate_random_string(10)
    user_info = register_user(username, password)
    token = login_user(username, password)
    return username, password, user_info, token

def test_retrieve_admin_post_by_user(registered_user):
    _, _, _, token = registered_user

    # adminのprivateな投稿を取得
    post_by_admin = get_post_by_id("1", token)

    assert "Welcome to admin private blog!" == post_by_admin["title"]
    assert "flag" in post_by_admin["content"]

def test_get_user_profile(registered_user):
    _, _, _, token = registered_user

    # adminのプロフィール情報を取得
    admin_user = get_user_profile_by_id("1", token)

    assert "admin" == admin_user["username"]
    assert "flag" in admin_user["image_url"]