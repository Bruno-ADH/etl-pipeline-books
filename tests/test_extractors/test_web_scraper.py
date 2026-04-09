"""
Tests unitaires — BookScraper
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from src.extractors.web_scraper import BookScraper, RATING_MAP

# HTML minimal simulant une page books.toscrape.com
FAKE_PAGE_HTML = """
<html>
<body>
  <article class="product_pod">
    <h3><a href="book1" title="A Great Book">A Great Book</a></h3>
    <p class="price_color">£12.99</p>
    <p class="star-rating Three"></p>
    <p class="instock availability">In stock</p>
  </article>
  <article class="product_pod">
    <h3><a href="book2" title="Another Book">Another Book</a></h3>
    <p class="price_color">£8.50</p>
    <p class="star-rating Five"></p>
    <p class="instock availability">  Out of stock  </p>
  </article>
</body>
</html>
"""


class TestBookScraper:

    def test_rating_map_completeness(self):
        """Les 5 niveaux de rating doivent être mappés."""
        assert len(RATING_MAP) == 5
        assert RATING_MAP["One"] == 1
        assert RATING_MAP["Five"] == 5

    def test_parse_book_extracts_fields(self):
        """_parse_book doit extraire titre, prix, rating, catégorie, stock."""
        scraper = BookScraper()
        soup = BeautifulSoup(FAKE_PAGE_HTML, "lxml")
        articles = soup.find_all("article", class_="product_pod")

        book = scraper._parse_book(articles[0], category="mystery")
        assert book["title"] == "A Great Book"
        assert book["price"] == 12.99
        assert book["rating"] == 3
        assert book["category"] == "mystery"
        assert book["in_stock"] is True

    def test_parse_book_out_of_stock(self):
        """Le champ in_stock doit être False quand le livre n'est pas disponible."""
        scraper = BookScraper()
        soup = BeautifulSoup(FAKE_PAGE_HTML, "lxml")
        articles = soup.find_all("article", class_="product_pod")

        book = scraper._parse_book(articles[1], category="fiction")
        assert book["in_stock"] is False

    def test_get_category_from_url(self):
        """L'extraction de catégorie depuis l'URL doit fonctionner."""
        scraper = BookScraper()
        url = "https://books.toscrape.com/catalogue/category/books/mystery_3/page-2.html"
        assert scraper._get_category_from_url(url) == "mystery"

    def test_get_category_from_url_unknown(self):
        """URL sans catégorie doit retourner 'unknown'."""
        scraper = BookScraper()
        assert scraper._get_category_from_url("https://books.toscrape.com/") == "unknown"

    @patch("src.extractors.web_scraper.BookScraper._fetch_page")
    def test_scrape_returns_dataframe(self, mock_fetch):
        """scrape() doit retourner un DataFrame non vide."""
        # Simuler une page avec 2 livres, puis None (pas de page suivante)
        soup = BeautifulSoup(FAKE_PAGE_HTML, "lxml")
        mock_fetch.return_value = soup

        scraper = BookScraper(max_pages=1)
        df = scraper.scrape()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "title" in df.columns
        assert "price" in df.columns
        assert "rating" in df.columns

    @patch("src.extractors.web_scraper.BookScraper._fetch_page")
    def test_scrape_handles_fetch_error(self, mock_fetch):
        """Une erreur réseau doit être gérée sans crasher."""
        mock_fetch.side_effect = Exception("Connexion refusée")

        scraper = BookScraper(max_pages=1)
        df = scraper.scrape()

        # Retourne un DataFrame vide au lieu de crasher
        assert isinstance(df, pd.DataFrame)
