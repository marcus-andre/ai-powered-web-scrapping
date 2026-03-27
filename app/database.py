import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv # Added to load env variables

# Load environment variables from .env file
load_dotenv()

# Get the Database URL from the environment
# Defaults to None if not found, preventing hardcoded leaks
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Create the engine instance
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency to provide a database session.
    Ensures connection lifecycle is managed professionally.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()