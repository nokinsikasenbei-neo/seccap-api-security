from sqlalchemy import create_engine, Column, Integer, String, Sequence, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    username = Column(String(50))
    sub = Column(String(50))
    role = Column(String(50))
    hashed_password = Column(String(100))
    image_url = Column(String(100))

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, Sequence('post_id_seq'), primary_key=True)
    title = Column(String(100))
    content = Column(String(500))
    user_id = Column(Integer)
    username = Column(String(50))
    is_private = Column(Boolean, default=False)
