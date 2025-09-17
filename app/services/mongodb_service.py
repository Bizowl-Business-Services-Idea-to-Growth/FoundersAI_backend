from typing import List, Dict, Any
from datetime import datetime
from app.core.database import db

collection = db["user_responses"]  # collection name

async def save_user_responses(user_id: str, responses: list, questions: list):
    # Combine each response with its question text from questions list by matching id
    enhanced_responses = []
    questions_map = {q["id"]: q for q in questions}

    for resp in responses:
        q = questions_map.get(resp["id"])
        question_text = q.get("question") if q else ""
        enhanced_responses.append({
            "id": resp["id"],
            "type": resp["type"],
            "question": question_text,
            "answer": resp["answer"]
        })

    document = {
        "userId": user_id,
        "responses": enhanced_responses,
        "timestamp": datetime.utcnow()
    }
    await collection.insert_one(document)

async def get_user_responses(user_id: str):
    return await collection.find_one({"userId": user_id})
