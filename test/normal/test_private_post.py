import requests
import secrets
import string
import pytest

BASE_URL = "http://localhost:8000"

def generate_random_string(length: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def register_user(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/user/register/", json=payload)
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
    response = requests.post(f"{BASE_URL}/user/login/", data=data)
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

def test_user_registration_and_private_post():
    # ユーザーA、Bの登録
    userA_username = generate_random_string(10)
    userA_password = generate_random_string(10)
    userB_username = generate_random_string(10)
    userB_password = generate_random_string(10)

    userA_info = register_user(userA_username, userA_password)
    assert 'username' in userA_info
    assert userA_info['username'] == userA_username
    
    userB_info = register_user(userB_username, userB_password)
    assert 'username' in userB_info
    assert userB_info['username'] == userB_username

    # ユーザーAでログイン
    tokenA = login_user(userA_username, userA_password)
    assert isinstance(tokenA, str)
    assert len(tokenA) > 0

    # ユーザーAがプライベートな投稿
    post = create_private_post("Private Title", "Private Content", tokenA)
    assert 'id' in post

    # ユーザーAでそのプライベートな投稿を閲覧
    post_by_A = get_post_by_id(post["id"], tokenA)[0]
    assert post_by_A['id'] == post['id']
    assert post_by_A['title'] == "Private Title"
    assert post_by_A['content'] == "Private Content"
    assert post_by_A['is_private'] == True

    # ユーザーBでログイン
    tokenB = login_user(userB_username, userB_password)
    assert isinstance(tokenB, str)
    assert len(tokenB) > 0

    # ユーザーBがユーザーAのプライベートな投稿を試みて閲覧
    post_by_B = get_post_by_id(post["id"], tokenB)
    assert post_by_B['detail'] == "Access to private post denied"