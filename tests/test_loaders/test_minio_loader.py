"""
Tests unitaires — MinIOLoader
"""

import pytest
import pandas as pd
import io
from unittest.mock import MagicMock, patch, call

from src.loaders.minio_loader import MinIOLoader


@pytest.fixture
def mock_minio_client():
    """Client MinIO mocké."""
    client = MagicMock()
    client.bucket_exists.return_value = True
    return client


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "title": ["Book A", "Book B"],
        "price": [9.99, 12.50],
        "rating": [4, 5],
    })


class TestMinIOLoaderSave:

    def test_save_calls_put_object(self, mock_minio_client, sample_df):
        """save() doit appeler put_object une fois."""
        loader = MinIOLoader(client=mock_minio_client)
        loader.save(sample_df, source="books_web", layer="bronze")
        mock_minio_client.put_object.assert_called_once()

    def test_save_returns_path_string(self, mock_minio_client, sample_df):
        """save() doit retourner une chaîne chemin non vide."""
        loader = MinIOLoader(client=mock_minio_client)
        path = loader.save(sample_df, source="books_web", layer="bronze")
        assert isinstance(path, str)
        assert "bronze" in path
        assert "books_web" in path

    def test_save_creates_bucket_if_missing(self, sample_df):
        """Si le bucket n'existe pas, make_bucket doit être appelé."""
        client = MagicMock()
        client.bucket_exists.return_value = False

        loader = MinIOLoader(client=client)
        loader.save(sample_df, source="weather", layer="silver")

        client.make_bucket.assert_called_once()

    def test_save_silver_layer(self, mock_minio_client, sample_df):
        """save() sur le layer silver doit utiliser le bon bucket."""
        loader = MinIOLoader(client=mock_minio_client)
        path = loader.save(sample_df, source="books_web", layer="silver")
        assert "silver" in path

    def test_save_gold_layer(self, mock_minio_client, sample_df):
        """save() sur le layer gold doit utiliser le bon bucket."""
        loader = MinIOLoader(client=mock_minio_client)
        path = loader.save(sample_df, source="books_by_category", layer="gold")
        assert "gold" in path


class TestMinIOLoaderLoad:

    def test_load_returns_dataframe(self, mock_minio_client, sample_df):
        """load() doit retourner un DataFrame."""
        # Sérialiser sample_df en Parquet pour simuler la réponse MinIO
        import pyarrow as pa
        import pyarrow.parquet as pq
        buffer = io.BytesIO()
        pq.write_table(pa.Table.from_pandas(sample_df), buffer)
        buffer.seek(0)

        mock_response = MagicMock()
        mock_response.read.return_value = buffer.read()
        mock_minio_client.get_object.return_value = mock_response

        loader = MinIOLoader(client=mock_minio_client)
        df = loader.load("bronze", "books_web/2024/01/15/books_web_20240115.parquet")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_list_objects_returns_list(self, mock_minio_client):
        """list_objects() doit retourner une liste."""
        obj1 = MagicMock()
        obj1.object_name = "books_web/2024/01/15/file.parquet"
        obj2 = MagicMock()
        obj2.object_name = "books_web/2024/01/16/file.parquet"
        mock_minio_client.list_objects.return_value = [obj1, obj2]

        loader = MinIOLoader(client=mock_minio_client)
        result = loader.list_objects("bronze", "books_web")

        assert isinstance(result, list)
        assert len(result) == 2

    def test_load_latest_raises_if_empty(self, mock_minio_client):
        """load_latest() doit lever FileNotFoundError si aucun fichier."""
        mock_minio_client.list_objects.return_value = []

        loader = MinIOLoader(client=mock_minio_client)
        with pytest.raises(FileNotFoundError):
            loader.load_latest("bronze", "books_web")
