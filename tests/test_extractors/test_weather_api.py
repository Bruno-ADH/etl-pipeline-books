"""
Tests unitaires — WeatherAPIExtractor
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.extractors.weather_api import WeatherAPIExtractor


# Réponse JSON simulée de l'API Open-Meteo
FAKE_API_RESPONSE = {
    "latitude": 48.8566,
    "longitude": 2.3522,
    "timezone": "Europe/Paris",
    "hourly": {
        "time": ["2024-01-15T00:00", "2024-01-15T01:00", "2024-01-15T02:00"],
        "temperature_2m": [5.2, 4.8, 4.5],
        "relative_humidity_2m": [82, 85, 87],
        "precipitation": [0.0, 0.1, 0.0],
        "wind_speed_10m": [12.5, 11.0, 10.8],
        "weather_code": [1, 2, 1],
    },
}


class TestWeatherAPIExtractor:

    @patch("src.extractors.weather_api.httpx.Client")
    def test_extract_returns_dataframe(self, mock_client_cls):
        """extract() doit retourner un DataFrame avec les données météo."""
        # Configurer le mock
        mock_response = MagicMock()
        mock_response.json.return_value = FAKE_API_RESPONSE
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        extractor = WeatherAPIExtractor()
        df = extractor.extract()

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    @patch("src.extractors.weather_api.httpx.Client")
    def test_extract_contains_city_column(self, mock_client_cls):
        """Le DataFrame doit contenir la colonne 'city'."""
        mock_response = MagicMock()
        mock_response.json.return_value = FAKE_API_RESPONSE
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        extractor = WeatherAPIExtractor()
        df = extractor.extract()

        assert "city" in df.columns
        assert "temperature_2m" in df.columns
        assert "precipitation" in df.columns

    @patch("src.extractors.weather_api.httpx.Client")
    def test_extract_handles_api_error(self, mock_client_cls):
        """Une erreur API ne doit pas faire crasher — retourne DataFrame vide."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("Timeout API")
        mock_client_cls.return_value = mock_client

        extractor = WeatherAPIExtractor()
        df = extractor.extract()

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_parse_city_response_empty_hourly(self):
        """Réponse sans données horaires doit retourner un DataFrame vide."""
        extractor = WeatherAPIExtractor()
        df = extractor._parse_city_response("Paris", {"hourly": {}})
        assert df.empty

    def test_parse_city_response_correct_rows(self):
        """Le nombre de lignes doit correspondre au nombre d'heures."""
        extractor = WeatherAPIExtractor()
        df = extractor._parse_city_response("Paris", FAKE_API_RESPONSE)
        # 3 heures dans le fake response
        assert len(df) == 3
        assert df["city"].iloc[0] == "Paris"
