from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Any
from app.core.database import db
from app.services.gemini_service import query_gemini
from app.services.mongodb_service import save_user_responses, get_user_responses


class MessageRequest(BaseModel):
    message: str


class ResponseItem(BaseModel):
    id: int
    type: str
    answer: Any


class SaveResponsesRequest(BaseModel):
    userId: str
    responses: List[ResponseItem]


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/users")
async def get_users():
    try:
        users = []
        cursor = db.users.find({})
        async for user in cursor:
            user['_id'] = str(user['_id'])
            users.append(user)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend")
async def get_recommendation(request: MessageRequest):
    try:
        # Get recommendation from Gemini
        recommendation = await query_gemini(request.message)
        
        # Store chat history in MongoDB
        chat_record = {
            "user_message": request.message,
            "ai_response": recommendation,
            "timestamp": datetime.utcnow(),
            "model": "gemini-1.5-flash"
        }
        
        # Insert into chats collection
        await db.chats.insert_one(chat_record)
        
        return {"recommendation": recommendation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat-history")
async def get_chat_history():
    try:
        chats = []
        cursor = db.chats.find({}).sort("timestamp", -1).limit(50)  # Get last 50 chats
        async for chat in cursor:
            chat['_id'] = str(chat['_id'])
            chats.append(chat)
        return {"chats": chats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save-responses")
async def save_responses(data: SaveResponsesRequest):
    try:
        await save_user_responses(data.userId, [resp.dict() for resp in data.responses])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-responses/{user_id}")
async def fetch_responses(user_id: str):
    document = await get_user_responses(user_id)
    if document:
        document["_id"] = str(document["_id"])  # Convert ObjectId to string
        return document
    else:
        raise HTTPException(status_code=404, detail="User responses not found")
