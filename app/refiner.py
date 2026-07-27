import logging
import re
import html
from .database_mongo import raw_data_collection
from .database_pgsql import SessionLocal
from .models import Product
import json
from app.services.ai_enrichment import analyze_content_with_gemini
import time
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def enrich_description_safely(description: str) -> tuple[str | None, str | None, str | None]:
    """
    Safely wraps the AI Gemini call. 
    Returns a tuple: (summary, sentiment, entities_json_string).
    If the API fails, it logs the error and returns None to prevent pipeline crash.
    """
    if not description:
        return None, None, None

    try:
        ai_result = analyze_content_with_gemini(raw_text=description)

        # Convert the list of strings into a JSON string to save in PostgreSQL
        entities_str = json.dumps(
            ai_result.key_entities) if ai_result.key_entities else None

        return ai_result.summary, ai_result.sentiment, entities_str

    except Exception as e:
        logging.error(f"AI Enrichment API failed during refinement: {e}")
        return None, None, None


def fix_encoding(text: str) -> str:
    """Repairs double-encoded UTF-8 strings (mojibake) coming from raw data."""
    if not text:
        return text
    try:
        # Re-encode to latin1 bytes and decode back as proper utf-8
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback if the string was already clean or properly encoded
        return text


def clean_title(title_str: str) -> str | None:
    if not title_str:
        return None

    # Step 0: Fix mojibake/encoding issues first
    title_str = fix_encoding(title_str)

    title_without_html = html.unescape(title_str)
    title_without_html_tags = re.sub(r'<[^>]*>', ' ', title_without_html)
    title_cleaned = " ".join(title_without_html_tags.split())

    if not title_cleaned:
        return None

    return title_cleaned


def clean_description(description_str: str) -> str | None:
    if not description_str:
        return None

    # Step 0: Fix mojibake/encoding issues first
    description_str = fix_encoding(description_str)

    description_without_html = html.unescape(description_str)
    description_without_html = re.sub(
        r'<[^>]*>', ' ', description_without_html)
    description_cleaned = description_without_html.strip()

    if not description_cleaned:
        return None

    return description_cleaned


def clean_url(url_str: str) -> str | None:
    if not url_str:
        return None

    return url_str.split('?')[0]


def clean_price(price_str: str) -> float | None:
    """Extracts a float value from a price string (e.g., '£51.77' -> 51.77)."""
    if not price_str:
        return None

    # Use regex to find numbers (including decimals) in the string
    match = re.search(r'[\d\.]+', price_str)
    if match:
        try:
            return float(match.group(0))
        except (ValueError, TypeError):
            return None
    return None


def clean_rating(rating_str: str) -> str | None:
    """Converts text ratings like 'Three' to numeric strings like '3'."""
    # Guard clause: return early if the input is None or empty
    if not rating_str:
        return None

    # Mapping dictionary to translate English text ratings into numeric strings
    rating_map = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5"
    }

    # Check if any mapped text exists in the target string (case-insensitive)
    for text_num, digit_str in rating_map.items():
        if text_num in rating_str.lower():
            return digit_str

    # Fallback: Regex to extract standard numeric digits if text mapping fails
    match = re.search(r'\d+[\d\.]*', rating_str)
    if match:
        return match.group(0)

    # Default return if no rating format is recognized
    return None


def process_bronze_to_gold():
    """
    Reads raw data from MongoDB (Bronze), cleans it, and inserts it into PostgreSQL (Gold).
    This process is idempotent: it will not insert duplicate records.
    """

    # Log process initiation for monitoring and debugging
    logging.info("Starting refinement process: Bronze -> Gold...")

    processed_count = 0
    skipped_count = 0

    # Establish a transactional session with the Gold layer (PostgreSQL)
    with SessionLocal() as db:
        # Extract all raw documents from the Bronze layer (MongoDB)
        raw_documents = raw_data_collection.find()

        for doc in raw_documents:
            # Parse raw data payload from the NoSQL document
            raw_data = doc.get("raw_data", {})
            url = raw_data.get("url")

            # Basic validation to ensure the source reference exists
            if not url:
                logging.warning(
                    f"Skipping document {doc['_id']} due to missing URL.")
                continue

            # # Query the Gold layer to ensure idempotency and prevent duplicate records
            exists = db.query(Product).filter(Product.url == url).first()
            if exists:
                skipped_count += 1
                continue

            # Perform data cleaning and normalization for titles and prices
            title_raw = raw_data.get("title")
            price_raw = raw_data.get("price")
            url_raw = raw_data.get("url")
            rating_raw = raw_data.get("rating")
            description_raw = raw_data.get("description")

            price_cleaned = clean_price(price_raw)
            title_cleaned = clean_title(title_raw)
            url_cleaned = clean_url(url_raw)
            rating_cleaned = clean_rating(rating_raw)
            description_cleaned = clean_description(description_raw)

            ai_summary, ai_sentiment, ai_entities = enrich_description_safely(
                description_cleaned)

            time.sleep(6)

            # Ensure only high-quality, complete records are promoted to the Gold layer.
            # Note: 'rating' and 'description' are purposely excluded from this strict check
            # because they are optional attributes in our API Data Contract. A product
            # remains perfectly valid for analysis even if it lacks a rating or description.
            if not all([title_cleaned, price_cleaned, url_cleaned]):
                logging.warning(
                    f"Skipping URL {url_cleaned} due to incomplete data after cleaning.")
                continue

            # Map refined data to the PostgreSQL relational model
            new_product = Product(
                title=title_cleaned,
                price=price_cleaned,
                url=url_cleaned,
                rating=rating_cleaned,
                description=description_cleaned,
                ai_summary=ai_summary,       # New AI Field
                ai_sentiment=ai_sentiment,   # New AI Field
                ai_entities=ai_entities      # New AI Field
            )

            try:
                # Add new record and commit transaction to the database
                db.add(new_product)
                db.commit()
                processed_count += 1
                logging.info(
                    f"Product refined and saved: {title_cleaned} | Price: {price_cleaned}")
            except Exception as e:
                # Rollback transaction on failure to maintain database integrity
                db.rollback()
                logging.error(f"Failed to save product from URL {url}: {e}")

    logging.info(
        f"Refinement process completed. New products: {processed_count}, Skipped (existing): {skipped_count}.")


if __name__ == "__main__":
    process_bronze_to_gold()
