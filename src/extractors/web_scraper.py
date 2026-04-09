"""
Extracteur Web — books.toscrape.com
Scrape titre, prix, catégorie, rating, disponibilité de tous les livres.
"""

import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger("web_scraper")

# Correspondance texte → nombre d'étoiles
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BookScraper:
    """Scrape tous les livres de books.toscrape.com page par page."""

    def __init__(self, base_url: str = None, max_pages: int = None):
        self.base_url = base_url or Config.BOOKS_URL
        self.max_pages = max_pages or Config.BOOKS_MAX_PAGES
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "ETL-Pipeline/1.0"})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_page(self, url: str) -> BeautifulSoup:
        """Télécharge une page et retourne le BeautifulSoup."""
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    def _parse_book(self, article, category: str) -> dict:
        """Extrait les données d'un article livre."""
        # Titre
        title = article.h3.a["title"]

        # Prix (ex: '£51.77' → 51.77)
        price_text = article.find("p", class_="price_color").text
        price = float(price_text.replace("£", "").replace("Â", "").strip())

        # Rating textuel → entier
        rating_tag = article.find("p", class_="star-rating")
        rating_classes = rating_tag.get("class", []) if rating_tag else []
        rating_class = next((cls for cls in rating_classes if cls != "star-rating"), None)
        rating = RATING_MAP.get(rating_class, 0)

        # Disponibilité
        availability = article.find("p", class_="instock availability").text.strip()
        in_stock = availability.lower() == "in stock"

        return {
            "title": title,
            "price": price,
            "rating": rating,
            "category": category,
            "in_stock": in_stock,
            "extracted_at": datetime.utcnow().isoformat(),
        }

    def _get_category_from_url(self, url: str) -> str:
        """Extrait le nom de catégorie depuis l'URL de pagination."""
        # ex: .../catalogue/category/books/mystery_3/page-2.html → mystery
        parts = url.split("/")
        for i, part in enumerate(parts):
            if part == "category" and i + 2 < len(parts):
                return parts[i + 2].rsplit("_", 1)[0]
        return "unknown"

    def scrape(self) -> pd.DataFrame:
        """
        Lance le scraping complet.

        Returns:
            DataFrame avec tous les livres extraits
        """
        all_books = []
        current_url = self.base_url
        page_count = 0

        logger.info("Début du scraping", extra={"url": self.base_url})

        while current_url and page_count < self.max_pages:
            try:
                soup = self._fetch_page(current_url)
                page_count += 1

                # Détecter la catégorie courante
                category = self._get_category_from_url(current_url)
                if category == "unknown":
                    # Page principale : pas de catégorie, on met 'general'
                    category = "general"

                # Parser chaque livre de la page
                articles = soup.find_all("article", class_="product_pod")
                for article in articles:
                    book = self._parse_book(article, category)
                    all_books.append(book)

                logger.info(
                    "Page scrapée",
                    extra={"page": page_count, "books_found": len(articles)},
                )

                # Lien vers la page suivante
                next_btn = soup.find("li", class_="next")
                if next_btn:
                    next_href = next_btn.a["href"]
                    # Construire l'URL absolue
                    if next_href.startswith("catalogue/"):
                        current_url = self.base_url + next_href
                    else:
                        base = current_url.rsplit("/", 1)[0]
                        current_url = f"{base}/{next_href}"
                else:
                    current_url = None

                # Pause polie entre les pages
                time.sleep(0.5)

            except Exception as e:
                logger.error(
                    "Erreur sur la page",
                    extra={"url": current_url, "error": str(e)},
                )
                break

        df = pd.DataFrame(all_books)
        logger.info(
            "Scraping terminé",
            extra={"total_books": len(df), "pages_scraped": page_count},
        )
        return df
