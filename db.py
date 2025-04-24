import os
import certifi
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv

# Load environment variables from .env file in development
if os.path.exists('.env'):
    load_dotenv()

# MongoDB connection details from environment variables or use default
MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://mihirpatel012024:IeHZklQmNZcWlBf4@cluster0.pfptbnu.mongodb.net/?ssl=true")
DB_NAME = os.environ.get('MONGO_DB_NAME', "Test")

# Create a MongoDB client with proper certificate verification
client = None
db = None

def get_db() -> Database:
    """
    Returns the database instance, initializing it if necessary
    """
    global client, db
    if client is None:
        try:
            # Initialize the MongoDB client
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            db = client[DB_NAME]
            # Test the connection
            client.admin.command('ping')
            print("MongoDB connection successful")
        except Exception as e:
            print(f"MongoDB connection error: {str(e)}")
            # If connection fails, return a dummy DB for development
            if os.environ.get('FLASK_ENV') != 'production':
                print("Using dummy DB for development")
                from pymongo.errors import ConnectionFailure
                raise ConnectionFailure(f"Could not connect to MongoDB: {str(e)}")

    return db
