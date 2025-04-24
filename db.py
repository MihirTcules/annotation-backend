import os
import certifi
from pymongo import MongoClient
from pymongo.database import Database

# MongoDB connection details
MONGO_URI = "mongodb+srv://mihirpatel012024:IeHZklQmNZcWlBf4@cluster0.pfptbnu.mongodb.net/?ssl=true"
DB_NAME = "Test"

# Create a MongoDB client with proper certificate verification
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client[DB_NAME]

def get_db() -> Database:
    """
    Returns the database instance
    """
    return db
