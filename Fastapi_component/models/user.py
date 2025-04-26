from pydantic import BaseModel
import hashlib


class UserInDB(BaseModel):
    username: str
    hashed_password: str


# 简单内存用户库
fake_user_db = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed
