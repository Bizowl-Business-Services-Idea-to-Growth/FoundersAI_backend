import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)

async def test():
    try:
        info = await client.server_info()
        print("Connected to MongoDB:", info)
    except Exception as e:
        print("Connection failed:", e)

asyncio.run(test())
