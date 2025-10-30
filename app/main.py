import os
import asyncio
from fastapi import FastAPI, HTTPException,Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Any
from app.core.database import db, ensure_indexes
from app.services.gemini_service import query_gemini, build_prompt_from_responses
from app.services.mongodb_service import (
    save_user_responses,
    get_latest_assessment,
    get_assessment,
    list_assessments,
    get_cached_roadmap,
    save_cached_roadmap,
)
from app.services.survey_data import steps
from app.api.auth import router as auth_router

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
    # Optional future: label/title field
    # title: Optional[str] = None


app = FastAPI()

# Add CORS middleware
raw_origins = os.getenv("FRONTEND_ORIGINS")
if raw_origins:
    allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
else:
    allow_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://founders-ai.vercel.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

@app.on_event("startup")
async def startup_event():
    await ensure_indexes()


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
#recommend
@app.post("/recommend")
async def get_recommendation(request: MessageRequest):
    try:
        recommendation = await query_gemini(request.message)

        chat_record = {
            "user_message": request.message,
            "ai_response": recommendation,
            "timestamp": datetime.utcnow(),
            "model": "gemini-flash-latest",
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
        assessment_id = await save_user_responses(data.userId, [resp.dict() for resp in data.responses], steps)
        return {"status": "success", "assessmentId": assessment_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assessments/{user_id}")
async def get_assessments(user_id: str):
    try:
        items = await list_assessments(user_id)
        return {"assessments": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-responses/{user_id}/{assessment_id}")
async def fetch_specific_assessment(user_id: str, assessment_id: str):
    document = await get_assessment(user_id, assessment_id)
    if document:
        document["_id"] = str(document.get("_id"))
        return document
    raise HTTPException(status_code=404, detail="Assessment not found")

@app.get("/get-responses/{user_id}")
async def fetch_latest_assessment(user_id: str):
    document = await get_latest_assessment(user_id)
    if document:
        document["_id"] = str(document.get("_id"))
        return document
    raise HTTPException(status_code=404, detail="No assessments found")


@app.get("/generate-roadmap/{user_id}")
async def generate_roadmap_latest(user_id: str, force: bool = False):
    latest = await get_latest_assessment(user_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No assessments found")
    return await _generate_for_assessment(user_id, latest.get("assessmentId"), latest, force)

@app.get("/generate-roadmap/{user_id}/{assessment_id}")
async def generate_roadmap_specific(user_id: str, assessment_id: str, force: bool = False):
    doc = await get_assessment(user_id, assessment_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return await _generate_for_assessment(user_id, assessment_id, doc, force)

async def _generate_for_assessment(user_id: str, assessment_id: str, assessment_doc: dict, force: bool):
    prompt = build_prompt_from_responses(assessment_doc)
    import hashlib, re
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    if not force:
        cached = await get_cached_roadmap(user_id, assessment_id)
        if cached and cached.get("prompt_hash") == prompt_hash:
            return {"roadmap": cached.get("raw", "")}

    def sanitize(text: str) -> str:
        return re.sub(r"\((?:sc|asc|xyz)\)", "", text)

    attempts = 0
    last_err = None
    while attempts < 2:
        attempts += 1
        try:
            roadmap_text = await query_gemini(prompt)
            cleaned = sanitize(roadmap_text)
            structured_ok = cleaned.strip().startswith('{') or cleaned.strip().startswith('[')
            await save_cached_roadmap(user_id, assessment_id, prompt_hash, cleaned, structured_ok)
            return {"roadmap": cleaned}
        except Exception as e:
            last_err = e
            print(f">>> DEBUG: Gemini attempt {attempts} failed for assessment {assessment_id}: {e}")
            await asyncio.sleep(0.5)
    raise HTTPException(status_code=500, detail=f"Gemini generation failed: {last_err}")
