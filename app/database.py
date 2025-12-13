import os
from motor.motor_asyncio import AsyncIOMotorClient

# Get DB URL from env, default to localhost for local dev if not in docker
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "genai_crud")

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DB_NAME]

async def get_database():
    return db
