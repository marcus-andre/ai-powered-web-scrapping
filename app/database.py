from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database connection URL configured for the Docker container network
SQLALCHEMY_DATABASE_URL = "postgresql://user_admin:password123@localhost:5432/web_collection_db"

# Create the engine to manage database connections
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session factory for creating local database session instances
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative data models
Base = declarative_base()

def get_db():
    """
    Dependency to provide a database session for each request.
    Ensures the connection is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()