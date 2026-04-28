import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from fake_useragent import UserAgent
import logging
from urllib.parse import urljoin
import os
# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import the MongoDB collection from our Bronze layer
from .database_mongo import raw_data_collection

# Initialize UserAgent to cache a list of real user agent strings
ua = UserAgent()

class ProductScraper:
    """
    Base class for web scraping operations.
    Designed for professional data extraction.
    """

    def __init__(self):
        # No static headers needed; they will be generated per request.
        pass

    def fetch_page(self, url: str) -> str | None:
        """Fetches the HTML content of a given URL."""
        try:
            headers = {'User-Agent': ua.random}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    def parse_product_data(self, html: str, url: str) -> dict | None:
        """Extracts product information from HTML (tailored for books.toscrape.com)."""
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            # Specific selectors for the target site
            title = soup.find('div', class_='product_main').find('h1').get_text(strip=True)
            price = soup.find('p', class_='price_color').get_text(strip=True)
            
            # Extract rating. The site uses classes like 'star-rating Three'
            rating_element = soup.find('p', class_='star-rating')
            rating = rating_element.get('class')[1] if rating_element and len(rating_element.get('class')) > 1 else None
            
            # Extract product description
            description = None
            desc_header = soup.find('div', id='product_description')
            if desc_header:
                desc_paragraph = desc_header.find_next_sibling('p')
                if desc_paragraph:
                    description = desc_paragraph.get_text(strip=True)

            data = {
                "title": title,
                "price": price,
                "url": url,
                "rating": rating,
                "description": description
            }
            return data
        except Exception as e:
            logging.error(f"Parsing error on {url}: {e}")
            return None

    def scrape_and_store(self, url: str):
        """Orchestrates the scraping process and stores the raw result in MongoDB."""
        logging.info(f"Scraping URL: {url}")
        
        html = self.fetch_page(url)
        if not html:
            return

        parsed_data = self.parse_product_data(html, url)
        if not parsed_data:
            return

        # Prepare the document for the Bronze layer
        bronze_document = {
            "source_url": url,
            "scraped_at": datetime.now(timezone.utc),
            "raw_data": parsed_data
        }

        # Insert into MongoDB
        result = raw_data_collection.insert_one(bronze_document)
        logging.info(f"Successfully stored raw data in MongoDB. Document ID: {result.inserted_id}")

    def crawl_catalog(self, start_url: str):
        """
        Crawls the product catalog implementing a scrap limit and deduplication logic.
        """
        # Fetch environment variable for scrape limit; default to 10
        limit = int(os.getenv("SCRAPE_LIMIT", "10"))
        scraped_count = 0

        # Load unique URLs from Bronze layer to prevent redundant scraping
        existing_urls = raw_data_collection.distinct("source_url")

        next_page_url = start_url
        page_num = 1

        while next_page_url and scraped_count < limit:
            logging.info(f"--- Scraping Catalog Page {page_num}: {next_page_url} ---")
            html = self.fetch_page(next_page_url)
            if not html:
                break

            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all product links on the current page
            product_links = soup.select('article.product_pod h3 a')

            for link in product_links:
                # Terminate loop if session limit is reached
                if scraped_count >= limit:
                    break
                # Construct the absolute URL for the product page
                product_url = urljoin(next_page_url, link['href'])

                # Deduplication check against local memory set
                if product_url in existing_urls:
                    logging.info(f"Skipping already scraped URL: {product_url}")
                    continue

                self.scrape_and_store(product_url)
                scraped_count += 1

            if scraped_count >= limit:
                break

            # Find the 'next' page link
            next_link_element = soup.select_one('li.next a')
            if next_link_element:
                next_page_url = urljoin(start_url, next_link_element['href'])
                page_num += 1
            else:
                next_page_url = None # No more pages, exit loop
        logging.info(f"Worker finished. New items collected: {scraped_count}")
        
# Quick test execution
if __name__ == "__main__":
    scraper = ProductScraper()
    start_url = "http://books.toscrape.com/catalogue/category/books_1/index.html"
    scraper.crawl_catalog(start_url)