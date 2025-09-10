from fastapi import FastAPI, HTTPException
from app.core.database import db

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
