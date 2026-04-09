"""
Loader MinIO — sauvegarde les DataFrames en Parquet dans les buckets Bronze/Silver/Gold.
"""

import io
from datetime import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from minio import Minio

from src.utils.config import Config
from src.utils.logger import get_logger
from src.utils.minio_client import get_minio_client, ensure_bucket_exists

logger = get_logger("minio_loader")


class MinIOLoader:
    """Sauvegarde et charge des DataFrames Parquet dans MinIO."""

    def __init__(self, client: Minio = None):
        self.client = client or get_minio_client()

    def _build_object_path(self, source: str, layer: str) -> str:
        """
        Construit le chemin d'objet avec partitionnement par date.
        Ex: books/2024/01/15/books_20240115_143022.parquet
        """
        now = datetime.utcnow()
        date_partition = now.strftime("%Y/%m/%d")
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        return f"{source}/{date_partition}/{source}_{timestamp}.parquet"

    def save(self, df: pd.DataFrame, source: str, layer: str) -> str:
        """
        Sauvegarde un DataFrame en Parquet dans le bucket spécifié.

        Args:
            df: DataFrame à sauvegarder
            source: Nom de la source (ex: 'books', 'weather', 'csv_books')
            layer: Couche cible ('bronze', 'silver', 'gold')

        Returns:
            Chemin complet de l'objet sauvegardé (bucket/path)
        """
        bucket = getattr(Config, f"MINIO_BUCKET_{layer.upper()}")
        ensure_bucket_exists(self.client, bucket)

        # Sérialiser en Parquet en mémoire
        table = pa.Table.from_pandas(df, preserve_index=False)
        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)
        size = buffer.getbuffer().nbytes

        object_path = self._build_object_path(source, layer)

        self.client.put_object(
            bucket_name=bucket,
            object_name=object_path,
            data=buffer,
            length=size,
            content_type="application/octet-stream",
        )

        full_path = f"{bucket}/{object_path}"
        logger.info(
            "Fichier sauvegardé dans MinIO",
            extra={
                "path": full_path,
                "rows": len(df),
                "size_bytes": size,
                "layer": layer,
            },
        )
        return full_path

    def load(self, bucket: str, object_path: str) -> pd.DataFrame:
        """
        Charge un fichier Parquet depuis MinIO.

        Args:
            bucket: Nom du bucket
            object_path: Chemin de l'objet dans le bucket

        Returns:
            DataFrame chargé
        """
        response = self.client.get_object(bucket, object_path)
        buffer = io.BytesIO(response.read())
        df = pd.read_parquet(buffer)
        logger.info(
            "Fichier chargé depuis MinIO",
            extra={"bucket": bucket, "path": object_path, "rows": len(df)},
        )
        return df

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """
        Liste les objets dans un bucket avec un préfixe donné.

        Args:
            bucket: Nom du bucket
            prefix: Préfixe de filtrage (ex: 'books/2024/01/')

        Returns:
            Liste des chemins d'objets
        """
        objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]

    def load_latest(self, bucket: str, source: str) -> pd.DataFrame:
        """
        Charge le fichier Parquet le plus récent pour une source donnée.

        Args:
            bucket: Nom du bucket
            source: Nom de la source (ex: 'books')

        Returns:
            DataFrame du fichier le plus récent
        """
        objects = self.list_objects(bucket, prefix=source)
        if not objects:
            raise FileNotFoundError(
                f"Aucun fichier trouvé dans {bucket}/{source}"
            )
        latest = sorted(objects)[-1]
        logger.info("Chargement du fichier le plus récent", extra={"path": latest})
        return self.load(bucket, latest)
