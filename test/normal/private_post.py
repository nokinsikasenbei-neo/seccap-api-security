import requests
import secrets
import string

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

if __name__ == "__main__":
    # ユーザーA、Bの登録
    userA_username = generate_random_string(10)
    userA_password = generate_random_string(10)
    userB_username = generate_random_string(10)
    userB_password = generate_random_string(10)

    register_user(userA_username, userA_password)
    print(f"Registered User A: {userA_username}")
    
    register_user(userB_username, userB_password)
    print(f"Registered User B: {userB_username}")

    # ユーザーAでログイン
    tokenA = login_user(userA_username, userA_password)
    print(f"User A Access Token: {tokenA}")

    # ユーザーAがプライベートな投稿
    post = create_private_post("Private Title", "Private Content", tokenA)
    print(f"Created Post by User A: {post}")

    # ユーザーAでそのプライベートな投稿を閲覧
    post_by_A = get_post_by_id(post["id"], tokenA)
    print(f"Retrieved Post by User A: {post_by_A}")

    # ユーザーBでログイン
    tokenB = login_user(userB_username, userB_password)
    print(f"User B Access Token: {tokenB}")

    # ユーザーBがユーザーAのプライベートな投稿を試みて閲覧
    post_by_B = get_post_by_id(post["id"], tokenB)
    print(f"Attempt to Retrieve Post by User B: {post_by_B}")