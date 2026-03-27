import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection string with local fallback
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user_admin:password123@localhost:5432/web_collection_db"
)

# Initialize SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Configure session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

# FastAPI dependency for database session management
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
