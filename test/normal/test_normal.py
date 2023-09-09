import requests
import secrets
import string
import pytest

# APIのベースURL
BASE_URL = "http://localhost:7000"  # FastAPIのデフォルトのアドレスとポート

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

# 投稿作成
def create_post(title, content, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": title, "content": content}
    response = requests.post(f"{BASE_URL}/post/create", headers=headers, json=payload)
    return response.json()

# 投稿取得
def get_post_by_id(post_id, token):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{BASE_URL}/post/{post_id}", headers=headers)
    return response.json()

# 投稿の一覧取得
def get_posts():
    response = requests.get(f"{BASE_URL}/posts/")
    return response.json()

# usernameとpasswordを生成
username = generate_random_string(10)
password = generate_random_string(10)

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

# 投稿作成
def test_create_post():
    token = login_user(username, password)
    title = "Test Title"
    content = "Test Content"
    post = create_post(title, content, token)
    assert post['title'] == title
    assert post['content'] == content

# 投稿取得
def test_get_post_by_id():
    token = login_user(username, password)
    post = create_post("Test Title", "Test Content", token)
    retrieved_post = get_post_by_id(post["id"], token)
    assert retrieved_post['title'] == post['title']
    assert retrieved_post['content'] == post['content']

# 投稿の一覧取得
def test_get_posts():
    posts = get_posts()
    assert isinstance(posts, list)
    assert len(posts) > 0
