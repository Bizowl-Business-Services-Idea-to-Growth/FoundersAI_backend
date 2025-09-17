import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pymongo import ASCENDING
from pymongo.errors import PyMongoError

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "founders_ai_db")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set in environment")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]


async def test_connection():
    try:
        await client.server_info()
        print(f"Connected to MongoDB database '{DB_NAME}'")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")


async def ensure_indexes():
    try:
        # Users: unique email
        await db.users.create_index("email", unique=True)
        # Responses: index on userId
        await db.user_responses.create_index([("userId", ASCENDING)])
        print("Indexes ensured")
    except PyMongoError as e:
        print(f"Index creation error: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
