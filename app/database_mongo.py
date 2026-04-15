import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load variables from .env if running outside Docker
load_dotenv()

# Fetch the variable injected by Docker or .env - no hardcoded strings here
MONGO_URL = os.getenv("MONGO_URL")

# Basic validation to ensure the infrastructure is correctly wired
if not MONGO_URL:
    raise ValueError("MONGO_URL environment variable is not set!")

client = MongoClient(MONGO_URL)

# Define the database and collection for the Bronze layer

# Access the specific database instance parsed from the connection string (MONGO_URL)
db = client.get_database() 
raw_data_collection = db["raw_html_payloads"]