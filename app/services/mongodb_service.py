from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["founders_ai_db"]  # use your actual DB name

collection = db["user_responses"]  # collection name

async def save_user_responses(user_id: str, responses: List[Dict[str, Any]]):
    document = {
        "userId": user_id,
        "responses": responses,
        "timestamp": datetime.utcnow()
    }
    await collection.insert_one(document)

async def get_user_responses(user_id: str):
    return await collection.find_one({"userId": user_id})
