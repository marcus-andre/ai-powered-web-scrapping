import os
from fastapi import FastAPI, Depends, Security, HTTPException, status, BackgroundTasks
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import text
from app.database_mongo import raw_data_collection
from apscheduler.schedulers.background import BackgroundScheduler
from .models import Product, ProductSchema
from .database_pgsql import engine, Base, get_db
from .models import Product
from .scraper import ProductScraper
from .refiner import process_bronze_to_gold


# Core API Instance
app = FastAPI(title="AI Powered Web Scrapping API")

# Database Initialization: Creates tables automatically on startup
Base.metadata.create_all(bind=engine)

# Background Scheduler Initialization
scheduler = BackgroundScheduler()
scheduler.start()

# API Key Security Configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)):
    """Validates the API Key provided in the request header."""
    expected_api_key = os.getenv("API_KEY")

    if not expected_api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Server API Key is not configured.")

    if api_key == expected_api_key:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate API credentials"
    )


def run_etl_pipeline():
    """Orchestrator function that runs the Scraper and then the Refiner."""
    import logging
    logging.info("Starting complete pipeline (Scraper -> Refiner)...")
    scraper = ProductScraper()
    scraper.crawl_catalog(
        "http://books.toscrape.com/catalogue/category/books_1/index.html")
    process_bronze_to_gold()


@app.post("/admin/clean-database")
def clean_database(api_key: str = Depends(get_api_key)):
    """
    Temporary endpoint to drop PostgreSQL table, clear MongoDB, 
    on Render production environment.
    """
    try:
        # 1. Drop Gold Table in PostgreSQL to recreate schema with new AI columns
        with engine.connect() as connection:
            connection.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
            connection.commit()

        # Recreate the tables right after dropping
        Base.metadata.create_all(bind=engine)

        # 2. Clear MongoDB Bronze collection
        raw_data_collection.delete_many({})

        return {
            "status": "success",
            "message": "Database reset and cleaned successfully!",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reset and clean: {str(e)}"
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


@app.post("/trigger-pipeline/", tags=["Actions"])
def trigger_pipeline(background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """
    Starts data collection and refinement immediately in the background.
    """
    background_tasks.add_task(run_etl_pipeline)
    return {"message": "Pipeline started in the background. Check the server logs."}


@app.post("/schedule-pipeline/", tags=["Actions"])
def schedule_pipeline(interval_minutes: int, api_key: str = Depends(get_api_key)):
    """
    Configures a schedule to run the pipeline every X minutes.
    """
    # Remove any previous schedule to avoid duplication
    scheduler.remove_all_jobs()

    # Add the new schedule
    scheduler.add_job(run_etl_pipeline, 'interval',
                      minutes=interval_minutes, id='pipeline_job')

    return {"message": f"Schedule configured! The bot will run every {interval_minutes} minutes."}
