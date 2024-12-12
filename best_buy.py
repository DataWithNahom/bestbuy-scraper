from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time
import random
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Selenium WebDriver configuration
options = webdriver.ChromeOptions()

# options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

class BestBuyScraper:
    def __init__(self, driver_path):
        logging.info("Initializing WebDriver")
        self.driver = webdriver.Chrome(service=Service(driver_path), options=options)

    def scrape(self, url):
        logging.info(f"Navigating to URL: {url}")
        self.driver.get(url)
        time.sleep(random.uniform(3, 5))

        # Handle international region selection
        if "Choose a country" in self.driver.page_source:
            logging.info("International region selection detected. Selecting United States...")
            try:
                us_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.us-link"))
                )
                us_button.click()
                logging.info("United States region selected successfully.")
                time.sleep(5)  
            except Exception as e:
                logging.error(f"Failed to select the region: {str(e)}")
                self._save_debug_data("region_selection_error.html", "region_selection_error.png")
                self.driver.quit()
                return []

        # Wait for the product page to load
        try:
            WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "li.sku-item"))
            )
        except Exception as e:
            logging.error(f"Elements not found after loading: {str(e)}")
            self._save_debug_data("error_page.html", "error_screenshot.png")
            self.driver.quit()
            return []

        products = []
        page_number = 1
        while True:
            logging.info(f"Scraping page {page_number}")
            product_containers = self.driver.find_elements(By.CSS_SELECTOR, "li.sku-item")

            if not product_containers:
                logging.error("No products found on this page.")
                self._save_debug_data("no_products_page.html", "no_products_screenshot.png")
                break

            for container in product_containers:
                try:
                    name = container.find_element(By.CSS_SELECTOR, "h4.sku-title a").text
                except Exception as e:
                    name = "N/A"
                    logging.warning(f"Failed to extract product name. Error: {e}")
                    logging.debug(f"Container HTML: {container.get_attribute('outerHTML')}")  

                try:
                    price = container.find_element(By.CSS_SELECTOR, "div.priceView-customer-price span").text
                except Exception:
                    price = "N/A"
                    logging.warning("Failed to extract product price")

                try:
                    image = container.find_element(By.CSS_SELECTOR, "img.product-image").get_attribute("src")
                except Exception:
                    image = "N/A"
                    logging.warning("Failed to extract product image")

                products.append({"name": name, "price": price, "image": image})

            logging.info(f"Extracted {len(product_containers)} products from page {page_number}")

            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next page']")
                if "disabled" in next_button.get_attribute("class"):
                    logging.info("No more pages to scrape")
                    break
                next_button.click()
                logging.info("Navigating to the next page")

                WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "li.sku-item"))
                )
                page_number += 1
            except Exception as e:
                logging.info(f"Pagination ended or an error occurred: {str(e)}")
                break

        self.driver.quit()
        logging.info("WebDriver closed")
        return products

    def save_to_json(self, data, filename="products.json"):
        logging.info(f"Saving data to {filename}")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info("Data saved successfully")

    def _save_debug_data(self, html_file, screenshot_file):
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        self.driver.save_screenshot(screenshot_file)
        logging.info(f"Saved debug data: {html_file}, {screenshot_file}")

if __name__ == "__main__":
    logging.info("Starting scraper")
    scraper = BestBuyScraper(driver_path="C:/Users/nahom/.wdm/drivers/chromedriver/win64/130.0.6723.91/chromedriver-win32/chromedriver.exe")
    url = "https://www.bestbuy.com/site/promo/iphone-16"
    scraped_data = scraper.scrape(url)

    scraper.save_to_json(scraped_data)
    logging.info("Scraping complete")
