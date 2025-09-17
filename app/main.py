from fastapi import FastAPI, HTTPException,Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Any
from app.core.database import db
from app.services.gemini_service import query_gemini, build_prompt_from_responses
from app.services.mongodb_service import save_user_responses, get_user_responses
from app.services.survey_data import steps

class CreateUserRequest(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

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
        "http://127.0.0.1:3000",
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
            user["_id"] = str(user["_id"])
            users.append(user)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-user", response_model=UserResponse)
async def create_user(user: CreateUserRequest = Body(...)):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user_doc = {
        "name": user.name,
        "email": user.email,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user_doc)
    created_user = await db.users.find_one({"_id": result.inserted_id})

    return UserResponse(
        id=str(created_user["_id"]),
        name=created_user["name"],
        email=created_user["email"],
    )

@app.post("/recommend")
async def get_recommendation(request: MessageRequest):
    try:
        recommendation = await query_gemini(request.message)

        chat_record = {
            "user_message": request.message,
            "ai_response": recommendation,
            "timestamp": datetime.utcnow(),
            "model": "gemini-1.5-flash",
        }

        await db.chats.insert_one(chat_record)

        return {"recommendation": recommendation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat-history")
async def get_chat_history():
    try:
        chats = []
        cursor = db.chats.find({}).sort("timestamp", -1).limit(50)
        async for chat in cursor:
            chat["_id"] = str(chat["_id"])
            chats.append(chat)
        return {"chats": chats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save-responses")
async def save_responses(data: SaveResponsesRequest):
    try:
        await save_user_responses(data.userId, [resp.dict() for resp in data.responses], steps)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-responses/{user_id}")
async def fetch_responses(user_id: str):
    document = await get_user_responses(user_id)
    if document:
        document["_id"] = str(document["_id"])
        return document
    else:
        raise HTTPException(status_code=404, detail="User responses not found")


@app.get("/generate-roadmap/{user_id}")
async def generate_roadmap(user_id: str):
    print(f">>> DEBUG: Received userId: {user_id}")
    user_data = await get_user_responses(user_id)
    if not user_data:
        print(f">>> DEBUG: No user responses found for userId: {user_id}")
        raise HTTPException(status_code=404, detail="User responses not found")
    else:
        print(f">>> DEBUG: User responses found: {user_data}")

    prompt = build_prompt_from_responses(user_data)

    try:
        roadmap_text = await query_gemini(prompt)
        return {"roadmap": roadmap_text}
    except Exception as e:
        print(f">>> DEBUG: Gemini API call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
