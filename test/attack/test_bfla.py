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

@pytest.fixture(scope="module")
def registered_user():
    username = generate_random_string(10)
    password = generate_random_string(10)
    user_info = register_user(username, password)
    token = login_user(username, password)
    return username, password, user_info, token

def get_secret1(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/secret1", headers=headers)
    return response.json()

def get_secret2(token, query):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/secret2?{query}", headers=headers)
    return response.json()

def test_get_secret1(registered_user):
    _, _, _, token = registered_user

    secret1 = get_secret1(token)
    assert 'flag' in secret1

def test_get_secret2(registered_user):
    _, _, _, token = registered_user

    secret2 = get_secret2(token, "role=guest")
    assert 'flag' not in secret2

    secret2 = get_secret2(token, "role=admin")
    assert 'flag' in secret2