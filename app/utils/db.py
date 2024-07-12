import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(override=True)
db_uri = os.getenv('MONGO_URI')
client = AsyncIOMotorClient(db_uri)
db = client['TrivAI']