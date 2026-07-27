import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch the variable injected by Docker or .env - no hardcoded strings here
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Basic validation to ensure the infrastructure is correctly wired
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

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
