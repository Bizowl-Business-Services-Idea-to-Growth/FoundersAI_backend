from fastapi import FastAPI, HTTPException, Request
from app.core.database import db
from app.services.gemini_service import query_gemini

from pydantic import BaseModel

class MessageRequest(BaseModel):
    message: str

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/users")
async def get_users():
    try:
        users = []
        cursor = db.users.find({})
        async for user in cursor:
            user['_id'] = str(user['_id'])  # Convert ObjectId for JSON
            users.append(user)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend")
async def get_recommendation(request: MessageRequest):
    body = await request.json()
    user_message = body["message"]
    recommendation = await query_gemini(user_message)
    return {"recommendation": recommendation}