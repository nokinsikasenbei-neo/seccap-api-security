from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from databases import Database
from models import Base, User, Post
from jose import JWTError, jwt
import secrets
import os
import httpx
import uuid
from urllib.parse import urlparse

app = FastAPI()

# Generate a random 128-bit SECRET_KEY
SECRET_KEY = secrets.token_hex(16)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600

DATABASE_URL = os.environ.get("DATABASE_URL")
database = Database(DATABASE_URL)
metadata = Base.metadata

# FLAG
BFLA_FLAG1 = os.environ.get("BFLA_FLAG1")
BFLA_FLAG2 = os.environ.get("BFLA_FLAG2")
BOLA_FLAG1 = os.environ.get("BOLA_FLAG1")
BOLA_FLAG2 = os.environ.get("BOLA_FLAG2")
SSRF_FLAG1 = os.environ.get("SSRF_FLAG1")
SSRF_FLAG2 = os.environ.get("SSRF_FLAG2")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login/")

class UserIn(BaseModel):
    username: str
    password: str

class UserImage(BaseModel):
    image_url: str

class PostCreate(BaseModel):
    title: str
    content: str
    is_private: bool = False

class PostOut(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    username: str
    is_private: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: str

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No access token provided")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        token_data = TokenData(sub=sub)
    except JWTError:
        raise credentials_exception

    query = User.__table__.select().where(User.sub == token_data.sub)
    user = await database.fetch_one(query)
    if user is None:
        raise credentials_exception
    return user

# 有効なURLであるかどうかを検証
def is_valid_url(value: str) -> bool:
    try:
        result = urlparse(value)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# URLのドメインがlocalhostでないことを検証
def is_not_localhost(hostname: str) -> bool:
    """
    Check if the given hostname is localhost.
    """
    return hostname not in ["localhost", "127.0.0.1", "::1"]

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# ユーザー用API
## ヘルスチェック
@app.get("/healthcheck", status_code=200)
def healthcheck():
    return {"status": "ok"}

## ユーザー登録
@app.post("/user/register", tags=["user"], status_code=201)
async def register(user: UserIn):
    # 既に同じユーザー名が存在する場合、エラーを投げる
    # query = User.__table__.select().where(User.username == user.username)
    # existing_user = await database.fetch_one(query)
    # if existing_user:
    #     raise HTTPException(status_code=400, detail="Username already exists.")
    
    # パスワードをハッシュ化してデータベースに保存
    hashed_password = get_password_hash(user.password)
    query = User.__table__.insert().values(username=user.username, hashed_password=hashed_password, sub=str(uuid.uuid4()))
    user_id = await database.execute(query)
    return {"id": user_id, "username": user.username}

## ログイン
@app.post("/user/login", tags=["user"], response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    query = User.__table__.select().where(User.username == form_data.username)
    users = await database.fetch_all(query)

    user = None
    for potential_user in users:
        if verify_password(form_data.password, potential_user.hashed_password):
            user = potential_user
            break

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.sub }, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

## ユーザーの画像を登録
@app.post("/user/image", tags=["user"], status_code=201)
async def register_user_image(image_data: UserImage, current_user: UserIn = Depends(get_current_user)):
    # 有効なURLであることを検証
    if not is_valid_url(image_data.image_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    # 画像URLをユーザーデータベースに保存
    query = User.__table__.update().where(User.id == current_user.id).values(image_url=image_data.image_url)
    await database.execute(query)
    return {"detail": "Image URL updated successfully"}

## ユーザーの画像を取得
@app.get("/user/image", tags=["user"])
async def get_user_image(current_user: UserIn = Depends(get_current_user)):
    query = User.__table__.select().where(User.id == current_user.id)
    user = await database.fetch_one(query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.image_url:
        raise HTTPException(status_code=404, detail="No image associated with this user")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(user.image_url)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch the image")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch the image")

    media_type = response.headers.get("Content-Type", "application/octet-stream")
    return StreamingResponse(BytesIO(response.content), media_type=media_type)  # Assuming the image is JPEG. Adjust as needed.

## ユーザーのプロフィールを取得
@app.get("/user/profile/{user_id}", tags=["user"])
async def get_user_profile(user_id: int, current_user: UserIn = Depends(get_current_user)):
    query = User.__table__.select().where(User.id == user_id)
    user = await database.fetch_one(query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

## 投稿の取得
@app.get("/post/{post_id}", tags=["post"])
async def get_post_by_id(post_id: int, current_user: str = Depends(get_current_user)):
    query = Post.__table__.select().where(Post.id == post_id)
    post = await database.fetch_one(query)

    if post == None:
        raise HTTPException(status_code=404, detail="Post not found")

    # postがprivateであり、postのusernameとcurrent_userのusernameが異なる場合、エラーを投げる
    if post.is_private and post.username != current_user.username:
        raise HTTPException(status_code=403, detail="Access to private post denied")

    return post

## 公開されている投稿の一覧を取得
@app.get("/posts", tags=["post"], response_model=List[PostOut])
async def get_posts(skip: int = 0, limit: int = 50):
    query = Post.__table__.select().where(Post.is_private == False).offset(skip).limit(limit)
    posts = await database.fetch_all(query)
    return posts

## 投稿の作成
@app.post("/post/create", tags=["post"], response_model=PostOut, status_code=201)
async def create_post(post: PostCreate, current_user: UserIn = Depends(get_current_user)):
    query = Post.__table__.insert().values(title=post.title, content=post.content, user_id=current_user.id, username = current_user.username, is_private=post.is_private)
    post_id = await database.execute(query)
    query = Post.__table__.select().where(Post.id == post_id)
    post = await database.fetch_one(query)
    return post

# 管理者用API
## ユーザーの一覧を取得
@app.get("/admin/users", tags=["admin"])
async def list_users(skip: int = 0, limit: int = 10, current_user: UserIn = Depends(get_current_user)):
    # roleがadminであることをチェック
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    query = User.__table__.select().offset(skip).limit(limit)
    users = await database.fetch_all(query)
    return users

## ユーザーの投稿を削除
@app.delete("/admin/post/delete/{post_id}", tags=["admin"], status_code=200)
async def delete_post(post_id: int, current_user: UserIn = Depends(get_current_user)):
    # roleがadminであることをチェック
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    query = Post.__table__.delete().where(Post.id == post_id)
    await database.execute(query)
    return {"detail": f"Post with id {post_id} deleted successfully"}

## 全ての投稿を取得
@app.get("/admin/all_posts", tags=["admin"])
async def get_all_posts(current_user: UserIn = Depends(get_current_user)):
    # roleがadminであることをチェック
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    query = Post.__table__.select()
    posts = await database.fetch_all(query)
    return posts

## シークレット情報を取得（1つ目）
@app.get("/admin/secret1", tags=["admin"])
async def get_secret_one():
    return {"flag": BFLA_FLAG1}

## シークレット情報を取得（2つ目）
@app.get("/admin/secret2", tags=["admin"])
async def get_secret_two(role: str = None, current_user: UserIn = Depends(get_current_user)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    return {"flag": BFLA_FLAG2}

# 内部呼び出し用API
## 内部ネットワーク情報を取得
@app.get("/internal/network", tags=["internal"])
async def get_internal_network_info(request: Request):
    # 内部からのアクセスでない場合、エラーを投げる
    client_host = request.client.host
    if client_host not in ("127.0.0.1", "::1"):
        raise HTTPException(status_code=403, detail="Not allowed!")
    
    return {
        "internal_network_info": {
            "db": "localhost:3306",
            "frontend": "localhost:5000",
            "api": "localhost:8000",
            "flag": SSRF_FLAG1
        }
    }

## 開発者情報を取得
@app.get("/internal/developer", tags=["internal"])
async def get_developer_info(request: Request):
    # 内部からのアクセスでない場合、エラーを投げる
    client_host = request.client.host
    if client_host not in ("127.0.0.1", "::1"):
        raise HTTPException(status_code=403, detail="Not allowed!")

    # URLのドメイン名がlocalhostであることを検証
    hostname = urlparse(str(request.url)).hostname
    if not is_not_localhost(hostname):
        raise HTTPException(status_code=400, detail="URL domain is localhost.")

    return {
        "developer_info": {
            "name": "Kenji Araki",
            "email": "kenji-a@email.example.com",
            "flag": SSRF_FLAG2
        }
    }