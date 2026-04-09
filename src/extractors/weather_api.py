"""
Extracteur API Open-Meteo
Récupère les données météo en temps réel pour plusieurs villes.
API gratuite, sans clé requise.
"""

import httpx
import pandas as pd
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger("weather_api")

# Variables météo à extraire depuis l'API
HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "weather_code",
]


class WeatherAPIExtractor:
    """Extrait les données météo depuis l'API Open-Meteo pour une liste de villes."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or Config.WEATHER_API_BASE_URL
        self.cities = Config.get_weather_cities()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_city(self, city: dict) -> dict:
        """
        Appelle l'API Open-Meteo pour une ville.

        Args:
            city: Dict avec 'name', 'lat', 'lon'

        Returns:
            Données brutes JSON de l'API
        """
        params = {
            "latitude": city["lat"],
            "longitude": city["lon"],
            "hourly": ",".join(HOURLY_VARIABLES),
            "forecast_days": 1,
            "timezone": "auto",
        }

        with httpx.Client(timeout=30) as client:
            response = client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

        logger.info("Météo récupérée", extra={"city": city["name"]})
        return data

    def _parse_city_response(self, city_name: str, data: dict) -> pd.DataFrame:
        """
        Transforme la réponse JSON en DataFrame.

        Args:
            city_name: Nom de la ville
            data: Réponse JSON de l'API

        Returns:
            DataFrame avec les données horaires
        """
        hourly = data.get("hourly", {})
        if not hourly:
            logger.warning("Aucune donnée horaire", extra={"city": city_name})
            return pd.DataFrame()

        df = pd.DataFrame(hourly)
        df.rename(columns={"time": "datetime"}, inplace=True)
        df["city"] = city_name
        df["latitude"] = data.get("latitude")
        df["longitude"] = data.get("longitude")
        df["timezone"] = data.get("timezone")
        df["extracted_at"] = datetime.utcnow().isoformat()

        return df

    def extract(self) -> pd.DataFrame:
        """
        Extrait les données météo pour toutes les villes configurées.

        Returns:
            DataFrame combiné de toutes les villes
        """
        all_frames = []

        logger.info(
            "Début extraction météo",
            extra={"cities": [c["name"] for c in self.cities]},
        )

        for city in self.cities:
            try:
                raw_data = self._fetch_city(city)
                df = self._parse_city_response(city["name"], raw_data)
                if not df.empty:
                    all_frames.append(df)
            except Exception as e:
                logger.error(
                    "Erreur extraction ville",
                    extra={"city": city["name"], "error": str(e)},
                )

        if not all_frames:
            logger.warning("Aucune donnée météo extraite")
            return pd.DataFrame()

        result = pd.concat(all_frames, ignore_index=True)
        logger.info(
            "Extraction météo terminée",
            extra={"total_rows": len(result), "cities": len(all_frames)},
        )
        return result
