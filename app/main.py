from fastapi import FastAPI
from .database import engine, Base
from .models import Product 

# Core API Instance
app = FastAPI(title="Web Collector Expert API")

# Database Initialization: Creates tables automatically on startup
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    """
    Service health check endpoint.
    """
    return {"status": "online", "system": "Web-Collector-Expert"}