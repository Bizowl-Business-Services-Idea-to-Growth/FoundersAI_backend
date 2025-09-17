from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.mongodb_service import save_user_responses, get_user_responses

router = APIRouter()

class ResponseItem(BaseModel):
    id: int
    type: str
    answer: Any

class SaveResponsesRequest(BaseModel):
    userId: str
    responses: List[ResponseItem]

@router.post("/save-responses")
async def save_responses(data: SaveResponsesRequest):
    try:
        await save_user_responses(data.userId, data.responses)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-responses/{user_id}")
async def fetch_responses(user_id: str):
    document = await get_user_responses(user_id)
    if document:
        return document
    else:
        raise HTTPException(status_code=404, detail="User responses not found")
