from typing import Any, Optional, List
from datetime import datetime
import uuid
from app.core.database import db

collection = db["user_responses"]  # user responses collection
roadmap_cache = db["roadmaps"]     # cached generated roadmaps

async def save_user_responses(user_id: str, responses: list, questions: list) -> str:
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

    assessment_id = str(uuid.uuid4())
    document = {
        "userId": user_id,
        "assessmentId": assessment_id,
        "responses": enhanced_responses,
        "created_at": datetime.utcnow()
    }
    await collection.insert_one(document)
    return assessment_id

async def get_latest_assessment(user_id: str):
    return await collection.find_one({"userId": user_id}, sort=[("created_at", -1)])

async def get_assessment(user_id: str, assessment_id: str):
    return await collection.find_one({"userId": user_id, "assessmentId": assessment_id})

async def list_assessments(user_id: str) -> List[dict]:
    cursor = collection.find({"userId": user_id}).sort("created_at", -1)
    results = []
    async for doc in cursor:
        results.append({
            "assessmentId": doc.get("assessmentId"),
            "created_at": doc.get("created_at"),
            "responses_count": len(doc.get("responses", []))
        })
    return results


# --------------- Roadmap caching ---------------
async def get_cached_roadmap(user_id: str, assessment_id: str) -> Optional[dict]:
    return await roadmap_cache.find_one({"userId": user_id, "assessmentId": assessment_id})

async def save_cached_roadmap(user_id: str, assessment_id: str, prompt_hash: str, raw_text: str, structured_ok: bool):
    doc = {
        "userId": user_id,
        "assessmentId": assessment_id,
        "prompt_hash": prompt_hash,
        "raw": raw_text,
        "structured_ok": structured_ok,
        "updated_at": datetime.utcnow()
    }
    await roadmap_cache.update_one({"userId": user_id, "assessmentId": assessment_id}, {"$set": doc}, upsert=True)
