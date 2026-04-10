"""
Transformer Silver → Gold
Agrégations, KPIs et statistiques pour Power BI.
"""

import pandas as pd
import numpy as np
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger("silver_aggregator")


class SilverAggregator:
    """Produit les agrégats Gold à partir des données Silver."""

    # ------------------------------------------------------------------ #
    #  LIVRES                                                              #
    # ------------------------------------------------------------------ #

    def aggregate_books_by_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        KPIs par catégorie de livre :
        - Nombre de livres
        - Prix moyen, min, max
        - Rating moyen
        - Pourcentage en stock
        """
        logger.info("Agrégation livres par catégorie", extra={"rows_in": len(df)})

        agg = (
            df.groupby("category", as_index=False)
            .agg(
                nb_books=("title", "count"),
                avg_price=("price", "mean"),
                min_price=("price", "min"),
                max_price=("price", "max"),
                avg_rating=("rating", "mean"),
            )
        )

        # Pourcentage en stock si la colonne existe
        if "in_stock" in df.columns:
            stock_rate = (
                df.groupby("category")["in_stock"]
                .mean()
                .reset_index()
                .rename(columns={"in_stock": "stock_rate"})
            )
            agg = agg.merge(stock_rate, on="category", how="left")

        agg["avg_price"] = agg["avg_price"].round(2)
        agg["avg_rating"] = agg["avg_rating"].round(2)
        agg["aggregated_at"] = datetime.utcnow().isoformat()
        agg["layer"] = "gold"

        logger.info("Agrégation terminée", extra={"categories": len(agg)})
        return agg

    def aggregate_books_price_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """Distribution des prix par tranche de 5£."""
        logger.info("Distribution des prix", extra={"rows_in": len(df)})

        df = df.copy()

        # Filtrer les lignes avec prix valide (non NaN, non négatif)
        df = df[df["price"].notna() & (df["price"] >= 0)]

        if df.empty:
            logger.warning("Aucune ligne avec prix valide")
            return pd.DataFrame(columns=["price_bucket", "nb_books", "avg_rating", "aggregated_at", "layer"])

        df["price_bucket"] = (df["price"] // 5 * 5).astype(int).astype(str) + "–" + (
            df["price"] // 5 * 5 + 5
        ).astype(int).astype(str) + "£"

        dist = (
            df.groupby("price_bucket", as_index=False)
            .agg(nb_books=("title", "count"), avg_rating=("rating", "mean"))
        )
        dist["avg_rating"] = dist["avg_rating"].round(2)
        dist["aggregated_at"] = datetime.utcnow().isoformat()
        dist["layer"] = "gold"
        return dist

    def aggregate_top_rated_books(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """Top N livres les mieux notés (ties inclus)."""
        logger.info(f"Top {top_n} livres", extra={"rows_in": len(df)})

        # Filtrer les lignes avec rating valide
        df_valid = df[df["rating"].notna()].copy()

        if df_valid.empty:
            logger.warning("Aucune ligne avec rating valide")
            return pd.DataFrame(columns=["title", "category", "price", "rating", "rank", "aggregated_at", "layer"])

        # Colonnes à sélectionner (in_stock peut ne pas exister)
        cols = ["title", "category", "price", "rating"]
        if "in_stock" in df_valid.columns:
            cols.append("in_stock")

        top = df_valid.nlargest(top_n, ["rating", "price"], keep="all")[cols].copy()
        top["rank"] = range(1, len(top) + 1)
        top["aggregated_at"] = datetime.utcnow().isoformat()
        top["layer"] = "gold"
        return top.reset_index(drop=True)

    # ------------------------------------------------------------------ #
    #  MÉTÉO                                                               #
    # ------------------------------------------------------------------ #

    def aggregate_weather_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Statistiques météo journalières par ville :
        - Température moy/min/max
        - Précipitations totales
        - Humidité moyenne
        - Vitesse vent moyenne
        """
        logger.info("Agrégation météo journalière", extra={"rows_in": len(df)})

        df = df.copy()
        if "datetime" in df.columns:
            df["date"] = pd.to_datetime(df["datetime"]).dt.date

        agg = (
            df.groupby(["city", "date"], as_index=False)
            .agg(
                avg_temp=("temperature_2m", "mean"),
                min_temp=("temperature_2m", "min"),
                max_temp=("temperature_2m", "max"),
                total_precipitation=("precipitation", "sum"),
                avg_humidity=("relative_humidity_2m", "mean"),
                avg_wind_speed=("wind_speed_10m", "mean"),
            )
        )

        for col in ["avg_temp", "min_temp", "max_temp", "avg_humidity", "avg_wind_speed"]:
            agg[col] = agg[col].round(1)
        agg["total_precipitation"] = agg["total_precipitation"].round(2)
        agg["aggregated_at"] = datetime.utcnow().isoformat()
        agg["layer"] = "gold"

        logger.info("Agrégation météo terminée", extra={"rows_out": len(agg)})
        return agg

    def aggregate_weather_city_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Résumé météo par ville (sur toute la période disponible)."""
        logger.info("Résumé météo par ville")

        agg = (
            df.groupby("city", as_index=False)
            .agg(
                avg_temp=("temperature_2m", "mean"),
                total_precipitation=("precipitation", "sum"),
                avg_humidity=("relative_humidity_2m", "mean"),
                avg_wind=("wind_speed_10m", "mean"),
                data_points=("datetime", "count"),
            )
        )

        for col in ["avg_temp", "avg_humidity", "avg_wind"]:
            agg[col] = agg[col].round(1)
        agg["total_precipitation"] = agg["total_precipitation"].round(2)
        agg["aggregated_at"] = datetime.utcnow().isoformat()
        agg["layer"] = "gold"
        return agg
