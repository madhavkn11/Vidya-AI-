import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client["studypal_course_platform"]

users_collection = db["users"]
courses_collection = db["courses"]
progress_collection = db["progress"]
chat_collection = db["chat_history"]
quiz_collection = db["quiz_attempts"]