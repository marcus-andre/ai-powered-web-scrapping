import logging
import os
from app.database_mongo import raw_data_collection
from app.database_pgsql import engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)


def reset_production_databases():
    """Drops the PostgreSQL Gold table and clears the MongoDB Bronze collection."""
    print("\n--- WARNING: RESETTING PRODUCTION DATABASES ---")

    # 1. Drop Gold Table in PostgreSQL (forces SQLAlchemy to recreate schema with new AI columns)
    try:
        with engine.connect() as connection:
            connection.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
            connection.commit()
            logging.info(
                "PostgreSQL: Table 'products' dropped successfully.")
    except Exception as e:
        logging.error(f"Failed to drop PostgreSQL table: {e}")

    # 2. Clear Bronze Collection in MongoDB
    try:
        result = raw_data_collection.delete_many({})
        logging.info(
            f"MongoDB: Cleared 'raw_data' collection. ({result.deleted_count} documents removed)")
    except Exception as e:
        logging.error(f"Failed to clear MongoDB collection: {e}")


if __name__ == "__main__":
    reset_production_databases()
