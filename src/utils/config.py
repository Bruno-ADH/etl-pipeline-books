"""
Configuration centralisée du pipeline ETL.
Charge les variables d'environnement et le fichier YAML.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Charger le .env s'il existe (développement local)
load_dotenv()


class Config:
    """Accès centralisé à toute la configuration du pipeline."""

    # --- MinIO ---
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_BUCKET_BRONZE: str = os.getenv("MINIO_BUCKET_BRONZE", "bronze")
    MINIO_BUCKET_SILVER: str = os.getenv("MINIO_BUCKET_SILVER", "silver")
    MINIO_BUCKET_GOLD: str = os.getenv("MINIO_BUCKET_GOLD", "gold")

    # --- Sources de données ---
    BOOKS_URL: str = os.getenv("BOOKS_URL", "https://books.toscrape.com/")
    BOOKS_MAX_PAGES: int = int(os.getenv("BOOKS_MAX_PAGES", "50"))

    CSV_FILE_PATH: str = os.getenv("CSV_FILE_PATH", "/opt/airflow/data/Books.csv")

    WEATHER_API_BASE_URL: str = os.getenv(
        "WEATHER_API_BASE_URL", "https://api.open-meteo.com/v1/forecast"
    )
    WEATHER_CITIES_RAW: str = os.getenv(
        "WEATHER_CITIES", "Paris,Montreal,Cotonou,New York,London"
    )

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

    @classmethod
    def get_weather_cities(cls) -> list[dict]:
        """Retourne la liste des villes avec leurs coordonnées GPS."""
        # Coordonnées fixes pour les villes supportées
        city_coords = {
            "Paris":     {"lat": 48.8566,  "lon": 2.3522},
            "Montreal":  {"lat": 45.5017,  "lon": -73.5673},
            "Cotonou":   {"lat": 6.3676,   "lon": 2.4252},
            "New York":  {"lat": 40.7128,  "lon": -74.0060},
            "London":    {"lat": 51.5074,  "lon": -0.1278},
        }
        cities = []
        for name in cls.WEATHER_CITIES_RAW.split(","):
            name = name.strip()
            coords = city_coords.get(name)
            if coords:
                cities.append({"name": name, **coords})
        return cities

    @classmethod
    def load_pipeline_config(cls) -> dict:
        """Charge le fichier YAML de configuration du pipeline."""
        config_path = Path(__file__).parents[2] / "config" / "pipeline_config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}
