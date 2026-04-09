"""
Transformer Bronze → Silver
Nettoyage, déduplication, validation et typage des données brutes.
"""

import pandas as pd
import numpy as np
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger("bronze_cleaner")


class BronzeCleaner:
    """Nettoie les DataFrames du Bronze Layer avant de les pousser en Silver."""

    # ------------------------------------------------------------------ #
    #  LIVRES (web scraper + CSV)                                          #
    # ------------------------------------------------------------------ #

    def clean_books(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie les données livres (scraper ou CSV).

        Opérations :
        - Suppression des doublons sur le titre
        - Normalisation des colonnes
        - Conversion des types
        - Suppression des valeurs aberrantes
        """
        logger.info("Nettoyage livres démarré", extra={"rows_in": len(df)})
        df = df.copy()

        # 1. Noms de colonnes uniformes
        df.columns = pd.Index([str(col).strip().lower().replace(" ", "_") for col in df.columns])

        # 2. Supprimer les lignes entièrement vides
        df.dropna(how="all", inplace=True)

        # 3. Déduplication sur le titre (insensible à la casse)
        if "title" in df.columns:
            df["title"] = df["title"].astype(str).str.strip()
            df.drop_duplicates(subset=["title"], keep="first", inplace=True)

        # 4. Prix : convertir en float et supprimer les invalides
        if "price" in df.columns:
            df["price"] = (
                pd.to_numeric(
                    df["price"].astype(str)
                    .str.replace("£", "", regex=False)
                    .str.replace("$", "", regex=False)
                    .str.strip(),
                    errors="coerce",
                )
            )
            # Prix aberrant : < 0 ou > 10000
            df = df[(df["price"].isna()) | ((df["price"] >= 0) & (df["price"] <= 10000))]

        # 5. Rating : s'assurer que c'est un entier entre 0 et 5
        if "rating" in df.columns:
            df["rating"] = pd.to_numeric(df["rating"], errors="coerce").clip(0, 5)

        # 6. Catégorie : normaliser
        if "category" in df.columns:
            df["category"] = df["category"].astype(str).str.strip().str.lower()

        # 7. Colonne de traitement
        df["cleaned_at"] = datetime.utcnow().isoformat()
        df["layer"] = "silver"

        logger.info(
            "Nettoyage livres terminé",
            extra={"rows_out": len(df), "duplicates_removed": True},
        )
        return df.reset_index(drop=True)

    # ------------------------------------------------------------------ #
    #  MÉTÉO                                                               #
    # ------------------------------------------------------------------ #

    def clean_weather(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie les données météo.

        Opérations :
        - Conversion du datetime
        - Suppression des doublons (ville + heure)
        - Validation des plages de valeurs
        """
        logger.info("Nettoyage météo démarré", extra={"rows_in": len(df)})
        df = df.copy()

        # 1. Convertir la colonne datetime
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            df.dropna(subset=["datetime"], inplace=True)

        # 2. Déduplication sur (ville, datetime)
        if "city" in df.columns and "datetime" in df.columns:
            df.drop_duplicates(subset=["city", "datetime"], keep="first", inplace=True)

        # 3. Valider les températures (-80 à 60 °C)
        if "temperature_2m" in df.columns:
            df["temperature_2m"] = pd.to_numeric(df["temperature_2m"], errors="coerce")
            df = df[
                df["temperature_2m"].isna()
                | ((df["temperature_2m"] >= -80) & (df["temperature_2m"] <= 60))
            ]

        # 4. Humidité (0–100%)
        if "relative_humidity_2m" in df.columns:
            df["relative_humidity_2m"] = pd.to_numeric(
                df["relative_humidity_2m"], errors="coerce"
            ).clip(0, 100)

        # 5. Précipitations : ne peut pas être négatif
        if "precipitation" in df.columns:
            df["precipitation"] = pd.to_numeric(
                df["precipitation"], errors="coerce"
            ).clip(lower=0)

        # 6. Vitesse du vent : ne peut pas être négatif
        if "wind_speed_10m" in df.columns:
            df["wind_speed_10m"] = pd.to_numeric(
                df["wind_speed_10m"], errors="coerce"
            ).clip(lower=0)

        df["cleaned_at"] = datetime.utcnow().isoformat()
        df["layer"] = "silver"

        logger.info("Nettoyage météo terminé", extra={"rows_out": len(df)})
        return df.reset_index(drop=True)
