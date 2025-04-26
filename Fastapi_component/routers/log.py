# routers/login_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from deps.deps import get_current_user
from routers.auth import create_access_token
from memory import history_pool

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    if req.username == "admin" and req.password == "123456":
        token = create_access_token({"sub": req.username})
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="用户名或密码错误")


@router.post("/logout")
def logout(current_user: str = Depends(get_current_user)):
    sessions = history_pool.get_user_sessions(current_user)
    for session_id in sessions:
        sessions[session_id].save_to_file(current_user, session_id)
    history_pool.clear_user_all_sessions(current_user)
    return {"msg": "已登出，历史已保存"}
