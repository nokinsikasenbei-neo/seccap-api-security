from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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

@app.post("/user/register/", status_code=201)
async def register(user: UserIn):
    query = User.__table__.select().where(User.username == user.username)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists.")
    
    hashed_password = get_password_hash(user.password)
    query = User.__table__.insert().values(username=user.username, hashed_password=hashed_password)
    user_id = await database.execute(query)
    return {"id": user_id, "username": user.username}

@app.post("/user/login/", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    query = User.__table__.select().where(User.username == form_data.username)
    user = await database.fetch_one(query)

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

@app.get("/posts/", response_model=List[PostOut])
async def get_posts(skip: int = 0, limit: int = 10):
    query = Post.__table__.select().offset(skip).limit(limit)
    posts = await database.fetch_all(query)
    return posts

@app.post("/post/create", response_model=PostOut, status_code=201)
async def create_post(post: PostCreate, current_user: UserIn = Depends(get_current_user)):
    query = Post.__table__.insert().values(title=post.title, content=post.content, user_id=current_user.id)
    post_id = await database.execute(query)
    query = Post.__table__.select().where(Post.id == post_id)
    post = await database.fetch_one(query)
    return post