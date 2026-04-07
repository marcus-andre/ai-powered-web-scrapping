from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from .database_pgsql import engine, Base, get_db
from .models import Product

# Pydantic schema para a resposta da API (um "Contrato de Dados")
# Isso garante que a API sempre retorne dados limpos e previsíveis.
class ProductSchema(BaseModel):
    id: int
    title: str
    price: float
    url: str
    collected_at: datetime

    class Config:
        from_attributes = True # Permite que o Pydantic leia dados de um modelo SQLAlchemy

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
    Recupera os produtos limpos da camada Gold (PostgreSQL).
    Este endpoint serve os dados finais de alta qualidade.
    """
    products = db.query(Product).offset(skip).limit(limit).all()
    return products