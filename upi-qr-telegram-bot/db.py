import motor.motor_asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.getenv("MONGO_URL")
if not mongo_url:
    raise ValueError("MONGO_URL is not set in the environment variables.")
    
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
db = client["FileReplace"]  # Replace with your desired database name
users_collection = db["users"]

async def collection_exists(collection_name):
    collections = await db.list_collection_names()
    return collection_name in collections

async def is_user_new(user_id: int) -> bool:
    user = await users_collection.find_one({"_id": user_id})
    return user is None

# Save the user to the database
async def save_user_to_db(user_id: int, user_name: str):
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"name": user_name}},
        upsert=True
    )
