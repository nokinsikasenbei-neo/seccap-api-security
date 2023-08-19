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

# 投稿取得
def get_post_by_id(post_id):
    response = requests.get(f"{BASE_URL}/post/{post_id}")
    return response.json()

# 投稿の一覧取得
def get_posts():
    response = requests.get(f"{BASE_URL}/posts/")
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
    post = get_post_by_id(post["id"])
    print(f"Post: {post}")
    
    # 投稿の一覧取得
    posts = get_posts()
    print(f"Posts: {posts}")