from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone # Added timezone
from .database import Base

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
    
    # Using the modern, timezone-aware approach
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))