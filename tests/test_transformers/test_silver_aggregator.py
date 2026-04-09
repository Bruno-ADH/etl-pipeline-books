"""
Tests unitaires — SilverAggregator
"""

import pytest
import pandas as pd
import numpy as np

from src.transformers.silver_aggregator import SilverAggregator


@pytest.fixture
def aggregator():
    return SilverAggregator()


@pytest.fixture
def silver_books_df():
    return pd.DataFrame({
        "title": [f"Book {i}" for i in range(10)],
        "category": ["fiction", "mystery", "fiction", "mystery", "sci-fi",
                     "fiction", "history", "mystery", "sci-fi", "history"],
        "price": [5.0, 12.0, 8.5, 15.0, 6.0, 9.0, 20.0, 11.0, 7.5, 18.0],
        "rating": [4, 5, 3, 4, 5, 2, 3, 4, 5, 1],
        "in_stock": [True, False, True, True, False, True, True, False, True, True],
    })


@pytest.fixture
def silver_weather_df():
    return pd.DataFrame({
        "datetime": pd.to_datetime([
            "2024-01-15T00:00", "2024-01-15T06:00", "2024-01-15T12:00",
            "2024-01-15T00:00", "2024-01-15T06:00",
        ]),
        "city": ["Paris", "Paris", "Paris", "London", "London"],
        "temperature_2m": [5.0, 7.0, 10.0, 3.0, 5.0],
        "precipitation": [0.0, 0.5, 0.2, 1.0, 0.3],
        "relative_humidity_2m": [80, 75, 70, 85, 82],
        "wind_speed_10m": [10.0, 12.0, 8.0, 15.0, 13.0],
    })


class TestAggregateBooksByCategory:

    def test_returns_dataframe(self, aggregator, silver_books_df):
        result = aggregator.aggregate_books_by_category(silver_books_df)
        assert isinstance(result, pd.DataFrame)

    def test_one_row_per_category(self, aggregator, silver_books_df):
        result = aggregator.aggregate_books_by_category(silver_books_df)
        categories = silver_books_df["category"].unique()
        assert len(result) == len(categories)

    def test_contains_kpi_columns(self, aggregator, silver_books_df):
        result = aggregator.aggregate_books_by_category(silver_books_df)
        for col in ["nb_books", "avg_price", "avg_rating"]:
            assert col in result.columns, f"Colonne manquante : {col}"

    def test_nb_books_correct(self, aggregator, silver_books_df):
        result = aggregator.aggregate_books_by_category(silver_books_df)
        fiction_row = result[result["category"] == "fiction"]
        assert fiction_row["nb_books"].iloc[0] == 3

    def test_layer_is_gold(self, aggregator, silver_books_df):
        result = aggregator.aggregate_books_by_category(silver_books_df)
        assert (result["layer"] == "gold").all()


class TestAggregateTopRatedBooks:

    def test_returns_top_n(self, aggregator, silver_books_df):
        result = aggregator.aggregate_top_rated_books(silver_books_df, top_n=5)
        assert len(result) <= 5

    def test_has_rank_column(self, aggregator, silver_books_df):
        result = aggregator.aggregate_top_rated_books(silver_books_df)
        assert "rank" in result.columns

    def test_rank_starts_at_1(self, aggregator, silver_books_df):
        result = aggregator.aggregate_top_rated_books(silver_books_df)
        assert result["rank"].iloc[0] == 1


class TestAggregateBooksPriceDistribution:

    def test_returns_dataframe(self, aggregator, silver_books_df):
        result = aggregator.aggregate_books_price_distribution(silver_books_df)
        assert isinstance(result, pd.DataFrame)

    def test_contains_price_bucket_column(self, aggregator, silver_books_df):
        result = aggregator.aggregate_books_price_distribution(silver_books_df)
        assert "price_bucket" in result.columns
        assert "layer" in result.columns
        assert (result["layer"] == "gold").all()

    def test_groups_books_into_buckets(self, aggregator, silver_books_df):
        result = aggregator.aggregate_books_price_distribution(silver_books_df)
        assert "5–10£" in result["price_bucket"].values
        bucket = result[result["price_bucket"] == "5–10£"]
        assert bucket["nb_books"].iloc[0] == 5


class TestAggregateWeatherDaily:

    def test_returns_dataframe(self, aggregator, silver_weather_df):
        result = aggregator.aggregate_weather_daily(silver_weather_df)
        assert isinstance(result, pd.DataFrame)

    def test_one_row_per_city_per_day(self, aggregator, silver_weather_df):
        result = aggregator.aggregate_weather_daily(silver_weather_df)
        # 2 villes × 1 jour = 2 lignes
        assert len(result) == 2

    def test_contains_temp_columns(self, aggregator, silver_weather_df):
        result = aggregator.aggregate_weather_daily(silver_weather_df)
        for col in ["avg_temp", "min_temp", "max_temp", "total_precipitation"]:
            assert col in result.columns

    def test_avg_temp_paris_correct(self, aggregator, silver_weather_df):
        result = aggregator.aggregate_weather_daily(silver_weather_df)
        paris = result[result["city"] == "Paris"]
        expected = round((5.0 + 7.0 + 10.0) / 3, 1)
        assert paris["avg_temp"].iloc[0] == expected


class TestAggregateWeatherCitySummary:

    def test_returns_dataframe(self, aggregator, silver_weather_df):
        result = aggregator.aggregate_weather_city_summary(silver_weather_df)
        assert isinstance(result, pd.DataFrame)

    def test_one_row_per_city(self, aggregator, silver_weather_df):
        result = aggregator.aggregate_weather_city_summary(silver_weather_df)
        assert len(result) == silver_weather_df["city"].nunique()

    def test_counts_data_points_per_city(self, aggregator, silver_weather_df):
        result = aggregator.aggregate_weather_city_summary(silver_weather_df)
        paris = result[result["city"] == "Paris"]
        assert paris["data_points"].iloc[0] == 3
