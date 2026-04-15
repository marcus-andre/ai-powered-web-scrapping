import os
from fastapi import FastAPI, Depends, Security, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from .database_pgsql import engine, Base, get_db
from .models import Product

# Pydantic schema for the API response (Data Contract). 
# Ensures the API always returns clean and predictable data.
class ProductSchema(BaseModel):
    id: int
    title: str
    price: float
    url: str
    rating: str | None
    description: str | None
    collected_at: datetime

    class Config:
        from_attributes = True # Allows Pydantic to read data from an SQLAlchemy model

# Core API Instance
app = FastAPI(title="Web Collector Expert API")

# Database Initialization: Creates tables automatically on startup
Base.metadata.create_all(bind=engine)

# API Key Security Configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    """Validates the API Key provided in the request header."""
    expected_api_key = os.getenv("API_KEY")
    
    if not expected_api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server API Key is not configured.")
        
    if api_key == expected_api_key:
        return api_key
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate API credentials"
    )

@app.get("/", tags=["Status"])
def read_root():
    """
    Service health check endpoint.
    """
    return {"status": "online", "system": "Web-Collector-Expert"}

@app.get("/products/", response_model=List[ProductSchema], tags=["Products"])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """
    Retrieves clean products from the Gold layer (PostgreSQL).
    This endpoint serves high-quality final data.
    """
    products = db.query(Product).offset(skip).limit(limit).all()
    return products