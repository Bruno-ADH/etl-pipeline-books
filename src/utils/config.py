"""
Configuration centralisee du pipeline ETL.
Charge les variables d'environnement et le fichier YAML.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Charger le .env s'il existe (developpement local)
load_dotenv()


def _load_pipeline_config() -> dict:
    """Charge le fichier YAML de configuration du pipeline."""
    config_path = Path(__file__).parents[2] / "config" / "pipeline_config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


PIPELINE_CONFIG = _load_pipeline_config()


def _get_config(path: str, default=None):
    """Recupere une valeur depuis le YAML via un chemin pointe."""
    value = PIPELINE_CONFIG
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


class Config:
    """Acces centralise a toute la configuration du pipeline."""

    # --- MinIO ---
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_BUCKET_BRONZE: str = os.getenv("MINIO_BUCKET_BRONZE", "bronze")
    MINIO_BUCKET_SILVER: str = os.getenv("MINIO_BUCKET_SILVER", "silver")
    MINIO_BUCKET_GOLD: str = os.getenv("MINIO_BUCKET_GOLD", "gold")

    # --- Sources de donnees ---
    BOOKS_URL: str = os.getenv(
        "BOOKS_URL", _get_config("extraction.books_web.url", "https://books.toscrape.com/")
    )
    BOOKS_MAX_PAGES: int = int(
        os.getenv("BOOKS_MAX_PAGES", str(_get_config("extraction.books_web.max_pages", 50)))
    )

    CSV_FILE_PATH: str = os.getenv("CSV_FILE_PATH", "/opt/airflow/data/Books.csv")

    WEATHER_API_BASE_URL: str = os.getenv(
        "WEATHER_API_BASE_URL",
        _get_config("extraction.weather.api_base_url", "https://api.open-meteo.com/v1/forecast"),
    )
    WEATHER_CITIES_RAW: str = os.getenv(
        "WEATHER_CITIES", "Paris,Montreal,Cotonou,New York,London"
    )

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", _get_config("logging.level", "INFO"))
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", _get_config("logging.format", "json"))

    @classmethod
    def get_weather_cities(cls) -> list[dict]:
        """Retourne la liste des villes avec leurs coordonnees GPS."""
        city_coords = {
            "Paris": {"lat": 48.8566, "lon": 2.3522},
            "Montreal": {"lat": 45.5017, "lon": -73.5673},
            "Cotonou": {"lat": 6.3676, "lon": 2.4252},
            "New York": {"lat": 40.7128, "lon": -74.0060},
            "London": {"lat": 51.5074, "lon": -0.1278},
        }

        yaml_cities = _get_config("extraction.weather.cities", [])
        if yaml_cities:
            city_coords = {
                city["name"]: {"lat": city["lat"], "lon": city["lon"]}
                for city in yaml_cities
                if all(k in city for k in ["name", "lat", "lon"])
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
        """Retourne le YAML de configuration deja charge."""
        return PIPELINE_CONFIG
