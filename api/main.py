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
import pdfkit

app = FastAPI()

# Generate a random 128-bit SECRET_KEY
SECRET_KEY = secrets.token_hex(16)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_URL = os.environ.get("DATABASE_URL")
database = Database(DATABASE_URL)
metadata = Base.metadata

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login/")

class UserIn(BaseModel):
    username: str
    password: str

class PostCreate(BaseModel):
    title: str
    content: str
    is_private: bool = False

class PostOut(BaseModel):
    id: int
    title: str
    content: str
    user_id: int

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str

class UserImage(BaseModel):
    image_url: str

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
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    query = User.__table__.select().where(User.username == token_data.username)
    user = await database.fetch_one(query)
    if user is None:
        raise credentials_exception
    return user

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
    # query = User.__table__.select().where(User.username == user.username)
    # existing_user = await database.fetch_one(query)
    # if existing_user:
    #     raise HTTPException(status_code=400, detail="Username already exists.")
    
    hashed_password = get_password_hash(user.password)
    query = User.__table__.insert().values(username=user.username, hashed_password=hashed_password)
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
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

## ユーザーの画像を登録
@app.post("/user/image", tags=["user"], status_code=201)
async def register_user_image(image_data: UserImage, current_user: UserIn = Depends(get_current_user)):
    # SSRFの脆弱性部分
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(image_data.image_url)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch the image from the provided URL.")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to fetch the image from the provided URL.")

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

    # SSRFの脆弱性部分
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
async def get_post_by_id(post_id: str, current_user: str = Depends(get_current_user)):
    raw_query = f"SELECT id, title, content, user_id, is_private FROM posts WHERE id = {post_id};"
    posts = await database.fetch_all(raw_query)

    if not posts:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = posts[0]

    # postのuser_idに関連付けられているusernameを取得する
    user_query = User.__table__.select().where(User.id == post.user_id)
    post_user = await database.fetch_one(user_query)

    # postがprivateであり、postのusernameとcurrent_userのusernameが異なる場合、エラーを投げる
    if post.is_private and post_user.username != current_user.username:
        raise HTTPException(status_code=403, detail="Access to private post denied")

    return posts

## 公開されている投稿の一覧を取得
@app.get("/posts", tags=["post"], response_model=List[PostOut])
async def get_posts(skip: int = 0, limit: int = 10):
    query = Post.__table__.select().where(Post.is_private == False).offset(skip).limit(limit)
    posts = await database.fetch_all(query)
    return posts

## 投稿の作成
@app.post("/post/create", tags=["post"], response_model=PostOut, status_code=201)
async def create_post(post: PostCreate, current_user: UserIn = Depends(get_current_user)):
    query = Post.__table__.insert().values(title=post.title, content=post.content, user_id=current_user.id, is_private=post.is_private)
    post_id = await database.execute(query)
    query = Post.__table__.select().where(Post.id == post_id)
    post = await database.fetch_one(query)
    return post

## 投稿をPDFにしてエクスポート
@app.get("/post/export/{post_id}", tags=["post"])
async def export_post_to_pdf(post_id: int, current_user: UserIn = Depends(get_current_user)):
    # postの情報を取得
    query = Post.__table__.select().where(Post.id == post_id)
    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # postがprivateであり、postのusernameとcurrent_userのusernameが異なる場合、エラーを投げる
    if post.is_private and post_user.username != current_user.username:
        raise HTTPException(status_code=403, detail="Access to private post denied")
    
    # postの情報をHTML形式でフォーマット
    html_content = f"""
    <html>
        <head>
            <title>{post.title}</title>
        </head>
        <body>
            <h1>{post.title}</h1>
            <p>{post.content}</p>
        </body>
    </html>
    """
    
    # HTMLをPDFに変換
    pdf = pdfkit.from_string(html_content, False)
    
    return StreamingResponse(BytesIO(pdf), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=post_{post_id}.pdf"})

# 管理者用API
## ユーザーの一覧を取得
@app.get("/admin/users", tags=["admin"])
async def list_users(request: Request, skip: int = 0, limit: int = 10):
    client_host = request.client.host
    if client_host not in ("127.0.0.1", "::1"):
        raise HTTPException(status_code=403, detail="Not allowed!")

    query = User.__table__.select().offset(skip).limit(limit)
    users = await database.fetch_all(query)
    return users

## ユーザーの投稿を削除
@app.delete("/admin/post/delete/{post_id}", tags=["admin"], status_code=200)
async def delete_post(post_id: int):
    query = Post.__table__.delete().where(Post.id == post_id)
    await database.execute(query)
    return {"detail": f"Post with id {post_id} deleted successfully"}

## 全ての投稿を取得
@app.get("/admin/all_posts", tags=["admin"])
async def get_all_posts():
    query = Post.__table__.select()
    posts = await database.fetch_all(query)
    return posts