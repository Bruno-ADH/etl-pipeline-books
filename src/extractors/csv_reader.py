"""
Extracteur CSV — fichier Books.csv
Lit le fichier CSV de métadonnées livres et le retourne en DataFrame.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger("csv_reader")


class CSVReader:
    """Lit et normalise le fichier CSV Books.csv."""

    def __init__(self, file_path: str = None):
        self.file_path = file_path or Config.CSV_FILE_PATH

    def extract(self) -> pd.DataFrame:
        """
        Lit le CSV et retourne un DataFrame normalisé.

        Returns:
            DataFrame avec les données du CSV

        Raises:
            FileNotFoundError: Si le fichier CSV est introuvable
        """
        path = Path(self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier CSV introuvable : {self.file_path}")

        logger.info("Lecture du CSV", extra={"path": str(path)})

        # Essayer différents encodages courants
        # low_memory=False pour éviter les types mixtes
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(path, encoding=encoding, on_bad_lines="skip", low_memory=False)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError(f"Impossible de lire le fichier CSV avec les encodages testés.")

        # Normaliser les noms de colonnes (minuscules, espaces → underscores)
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("-", "_")
        )

        # Convertir les colonnes object en string pour éviter les erreurs PyArrow
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str)

        # Ajouter la date d'extraction
        df["extracted_at"] = datetime.utcnow().isoformat()
        df["source"] = "csv"

        logger.info(
            "CSV lu avec succès",
            extra={"rows": len(df), "columns": list(df.columns)},
        )
        return df
