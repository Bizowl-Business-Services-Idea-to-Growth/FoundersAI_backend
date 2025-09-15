from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from app.core.database import db
from app.services.gemini_service import query_gemini

class MessageRequest(BaseModel):
    message: str

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
