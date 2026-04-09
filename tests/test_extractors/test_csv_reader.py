"""
Tests unitaires — CSVReader
"""

import pytest
import pandas as pd
import tempfile
import os

from src.extractors.csv_reader import CSVReader


@pytest.fixture
def sample_csv(tmp_path):
    """Crée un fichier CSV temporaire pour les tests."""
    csv_content = """Book-Title,Book-Author,Year-Of-Publication,Publisher,Price
The Great Gatsby,F. Scott Fitzgerald,1925,Scribner,9.99
1984,George Orwell,1949,Secker & Warburg,7.50
To Kill a Mockingbird,Harper Lee,1960,J. B. Lippincott,8.99
The Great Gatsby,F. Scott Fitzgerald,1925,Scribner,9.99
"""
    csv_file = tmp_path / "books_test.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    return str(csv_file)


class TestCSVReader:

    def test_extract_returns_dataframe(self, sample_csv):
        """extract() doit retourner un DataFrame."""
        reader = CSVReader(file_path=sample_csv)
        df = reader.extract()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_extract_normalizes_columns(self, sample_csv):
        """Les noms de colonnes doivent être en minuscules avec underscores."""
        reader = CSVReader(file_path=sample_csv)
        df = reader.extract()
        for col in df.columns:
            assert col == col.lower(), f"Colonne non normalisée : {col}"
            assert " " not in col, f"Espace dans la colonne : {col}"

    def test_extract_adds_metadata_columns(self, sample_csv):
        """Les colonnes extracted_at et source doivent être ajoutées."""
        reader = CSVReader(file_path=sample_csv)
        df = reader.extract()
        assert "extracted_at" in df.columns
        assert "source" in df.columns
        assert df["source"].iloc[0] == "csv"

    def test_extract_file_not_found(self):
        """FileNotFoundError si le fichier n'existe pas."""
        reader = CSVReader(file_path="/chemin/inexistant/books.csv")
        with pytest.raises(FileNotFoundError):
            reader.extract()

    def test_extract_correct_row_count(self, sample_csv):
        """Le CSV de test contient 4 lignes (dont 1 doublon)."""
        reader = CSVReader(file_path=sample_csv)
        df = reader.extract()
        # CSVReader lit tout (sans déduplication — c'est le rôle du BronzeCleaner)
        assert len(df) == 4
