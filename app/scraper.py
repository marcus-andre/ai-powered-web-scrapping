import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from fake_useragent import UserAgent

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
        """
        Fetches the HTML content of a given URL.
        """
        try:
            headers = {'User-Agent': ua.random}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            # Professional error logging
            print(f"Error fetching {url}: {e}")
            return None

    def parse_product_data(self, html: str, url: str) -> dict | None:
        """
        Extracts product information from HTML.
        This logic is tailored for books.toscrape.com for demonstration.
        """
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            # Specific selectors for the example site
            title = soup.find('div', class_='product_main').find('h1').get_text(strip=True)
            price = soup.find('p', class_='price_color').get_text(strip=True)
            
            data = {
                "title": title,
                "price": price,
                "url": url
            }
            return data
        except Exception as e:
            print(f"Parsing error on {url}: {e}")
            return None

    def scrape_and_store(self, url: str):
        """Orchestrates the scraping process and stores the raw result in MongoDB."""
        print(f"Scraping URL: {url}")
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
        print(f"Successfully stored raw data in MongoDB. Document ID: {result.inserted_id}")

# Quick test execution
if __name__ == "__main__":
    scraper = ProductScraper()
    test_url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    scraper.scrape_and_store(test_url)