from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from functions import query_ollama
from deps.deps import get_current_user

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str
    key: str


@router.post("/ask", response_class=StreamingResponse)
async def chat(req: ChatRequest, current_user: str = Depends(get_current_user)):
    return StreamingResponse(query_ollama(q=req.message, user_id=current_user, session_id=req.session_id, key=req.key),
                             media_type="text/plain")
