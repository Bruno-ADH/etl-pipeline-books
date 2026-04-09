"""
Tests unitaires — BronzeCleaner
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.transformers.bronze_cleaner import BronzeCleaner


@pytest.fixture
def cleaner():
    return BronzeCleaner()


@pytest.fixture
def sample_books_df():
    """DataFrame livres avec cas typiques : doublons, prix invalides, colonnes sales."""
    return pd.DataFrame({
        "title": [
            "Book A", "Book B", "Book A",  # doublon sur title
            "Book C", "Book D", None,       # valeur nulle
        ],
        "price": [12.99, -5.0, 12.99, 8.50, 99999.0, 5.0],  # négatif + aberrant
        "rating": [3, 5, 3, 2, 4, 1],
        "category": ["Fiction", "Mystery", "Fiction", "sci-fi", "History", "Romance"],
        "in_stock": [True, False, True, True, False, True],
    })


@pytest.fixture
def sample_weather_df():
    """DataFrame météo avec cas typiques."""
    return pd.DataFrame({
        "datetime": [
            "2024-01-15T00:00", "2024-01-15T01:00",
            "2024-01-15T00:00",  # doublon (même ville + heure)
            "2024-01-15T02:00", "invalid-date",
        ],
        "city": ["Paris", "Paris", "Paris", "London", "Dakar"],
        "temperature_2m": [5.2, 4.8, 5.2, 200.0, -90.0],  # 200 et -90 = aberrants
        "relative_humidity_2m": [82, 85, 82, 150, 60],  # 150 > 100
        "precipitation": [0.0, -0.5, 0.0, 1.2, 0.0],   # négatif
        "wind_speed_10m": [12.5, 11.0, 12.5, -5.0, 8.0],  # négatif
    })


class TestBronzeCleanerBooks:

    def test_removes_duplicates(self, cleaner, sample_books_df):
        """Les titres en double doivent être supprimés."""
        df = cleaner.clean_books(sample_books_df)
        assert df["title"].duplicated().sum() == 0

    def test_removes_negative_prices(self, cleaner, sample_books_df):
        """Les prix négatifs doivent être supprimés."""
        df = cleaner.clean_books(sample_books_df)
        assert (df["price"] < 0).sum() == 0

    def test_normalizes_category(self, cleaner, sample_books_df):
        """Les catégories doivent être en minuscules."""
        df = cleaner.clean_books(sample_books_df)
        for cat in df["category"].dropna():
            assert cat == cat.lower()

    def test_adds_cleaned_at_column(self, cleaner, sample_books_df):
        """La colonne cleaned_at doit être ajoutée."""
        df = cleaner.clean_books(sample_books_df)
        assert "cleaned_at" in df.columns

    def test_adds_layer_column(self, cleaner, sample_books_df):
        """La colonne layer doit valoir 'silver'."""
        df = cleaner.clean_books(sample_books_df)
        assert (df["layer"] == "silver").all()

    def test_returns_dataframe(self, cleaner, sample_books_df):
        """Le résultat doit toujours être un DataFrame."""
        result = cleaner.clean_books(sample_books_df)
        assert isinstance(result, pd.DataFrame)

    def test_empty_dataframe(self, cleaner):
        """Un DataFrame vide ne doit pas crasher."""
        df = cleaner.clean_books(pd.DataFrame())
        assert isinstance(df, pd.DataFrame)


class TestBronzeCleanerWeather:

    def test_converts_datetime(self, cleaner, sample_weather_df):
        """La colonne datetime doit être convertie en type datetime."""
        df = cleaner.clean_weather(sample_weather_df)
        assert pd.api.types.is_datetime64_any_dtype(df["datetime"])

    def test_removes_invalid_dates(self, cleaner, sample_weather_df):
        """Les datetimes invalides doivent être supprimés."""
        df = cleaner.clean_weather(sample_weather_df)
        assert df["datetime"].isna().sum() == 0

    def test_removes_duplicate_city_datetime(self, cleaner, sample_weather_df):
        """Les doublons (ville + heure) doivent être supprimés."""
        df = cleaner.clean_weather(sample_weather_df)
        assert df.duplicated(subset=["city", "datetime"]).sum() == 0

    def test_clips_humidity_to_100(self, cleaner, sample_weather_df):
        """L'humidité ne doit pas dépasser 100%."""
        df = cleaner.clean_weather(sample_weather_df)
        assert (df["relative_humidity_2m"] <= 100).all()

    def test_clips_precipitation_non_negative(self, cleaner, sample_weather_df):
        """Les précipitations ne peuvent pas être négatives."""
        df = cleaner.clean_weather(sample_weather_df)
        assert (df["precipitation"] >= 0).all()

    def test_clips_wind_speed_non_negative(self, cleaner, sample_weather_df):
        """La vitesse du vent ne peut pas être négative."""
        df = cleaner.clean_weather(sample_weather_df)
        assert (df["wind_speed_10m"] >= 0).all()
