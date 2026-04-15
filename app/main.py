from fastapi import FastAPI, Depends
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

@app.get("/", tags=["Status"])
def read_root():
    """
    Service health check endpoint.
    """
    return {"status": "online", "system": "Web-Collector-Expert"}

@app.get("/products/", response_model=List[ProductSchema], tags=["Products"])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves clean products from the Gold layer (PostgreSQL).
    This endpoint serves high-quality final data.
    """
    products = db.query(Product).offset(skip).limit(limit).all()
    return products