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

def get_post_by_id(post_id, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/post/{post_id}", headers=headers)
    return response.json()

def delete_post_by_id(post_id):
    response = requests.delete(f"{BASE_URL}/admin/post/delete/{post_id}")
    return response.json()

@pytest.fixture(scope="module")
def registered_users():
    userA_username = generate_random_string(10)
    userA_password = generate_random_string(10)
    userB_username = generate_random_string(10)
    userB_password = generate_random_string(10)

    register_user(userA_username, userA_password)
    register_user(userB_username, userB_password)

    tokenA = login_user(userA_username, userA_password)
    tokenB = login_user(userB_username, userB_password)
    return userA_username, userA_password, userB_username, userB_password, tokenA, tokenB

def test_create_retrieve_and_delete_post(registered_users):
    _, _, _, _, tokenA, tokenB = registered_users

    post = create_private_post("Private Title", "Private Content", tokenA)
    post_by_A = get_post_by_id(post["id"], tokenA)[0]
    
    # ユーザーAが作成した投稿を確認
    assert post["title"] == post_by_A["title"]
    assert post["content"] == post_by_A["content"]

    # ユーザーBがユーザーAのプライベート投稿を削除を試みる
    delete_response_by_B = delete_post_by_id(post["id"])
    assert delete_response_by_B["detail"] == f"Post with id {post['id']} deleted successfully"

    # ユーザーAがそのプライベート投稿を再度閲覧して、削除されていることを確認
    post_by_A_after_delete = get_post_by_id(post["id"], tokenA)
    assert post_by_A_after_delete["detail"] == "Post not found"