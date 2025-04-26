from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from deps.deps import get_current_user
from models.user import fake_user_db, UserInDB, hash_password, verify_password

router = APIRouter()

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ------------------- Pydantic Models -------------------

class Token(BaseModel):
    access_token: str
    token_type: str


class UserRegister(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ------------------- Token Helpers -------------------

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ------------------- Auth Routes -------------------

@router.post("/register", summary="用户注册")
def register(user: UserRegister):
    if user.username in fake_user_db:
        raise HTTPException(status_code=400, detail="用户已存在")
    fake_user_db[user.username] = UserInDB(
        username=user.username,
        hashed_password=hash_password(user.password)
    )
    return {"msg": "注册成功"}


@router.post("/login", response_model=Token, summary="JSON 登录（前端调用）")
def login_json(data: LoginRequest):
    user = fake_user_db.get(data.username)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token({"sub": data.username})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/token", response_model=Token, summary="表单登录（Swagger 使用）")
def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_user_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token({"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token, summary="刷新 Token")
def refresh_token(current_user: str = Depends(get_current_user)):
    token = create_access_token({"sub": current_user})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", summary="退出登录")
def logout(current_user: str = Depends(get_current_user)):
    return {"msg": f"{current_user} 已退出，Token 无效（实际项目中需加入黑名单机制）"}
