from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone # Added timezone
from .database_pgsql import Base
from pydantic import BaseModel, Field

class Product(Base):
    """
    SQLAlchemy model for the products table.
    Defines the schema for automated web scraping data storage.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    price = Column(Float)
    url = Column(String, unique=True)
    rating = Column(String)
    
    # Keeping the original description for fallback and detailed views
    description = Column(String)
    
    # AI Enriched Metadata
    ai_summary = Column(String, nullable=True)
    ai_sentiment = Column(String, nullable=True)
    ai_entities = Column(String, nullable=True) 
    
    # Using the modern, timezone-aware approach
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Pydantic schema for the API response (Data Contract). 
# Ensures the API always returns clean and predictable data.
class ProductSchema(BaseModel):
    id: int
    title: str
    price: float
    url: str
    rating: str | None
    description: str | None
    
    # Enriched fields
    ai_summary: str | None = None
    ai_sentiment: str | None = None
    ai_entities: str | None = None
    
    collected_at: datetime

    class Config:
        from_attributes = True # Allows Pydantic to read data from an SQLAlchemy model

# Pydantic schema enforcing structured JSON response from LLM
class DataAnalysisResult(BaseModel):
    summary: str = Field(description="Brief professional summary of the content in 2-3 sentences.")
    sentiment: str = Field(description="Overall sentiment: Positive, Neutral, or Negative.")
    key_entities: list[str] = Field(description="List of main topics or entities mentioned.")