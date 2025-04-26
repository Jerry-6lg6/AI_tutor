# deps/deps.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from core.security import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")  # Swagger 自动注入


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token invalid or out of date")
    return payload["sub"]
