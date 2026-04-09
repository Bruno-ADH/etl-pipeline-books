"""
Client MinIO partagé pour le pipeline ETL.
"""

from minio import Minio
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger("minio_client")


def get_minio_client() -> Minio:
    """
    Crée et retourne un client MinIO configuré.

    Returns:
        Instance Minio prête à l'emploi
    """
    # Extraire l'host:port depuis l'URL (ex: http://minio:9000 → minio:9000)
    endpoint = Config.MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
    secure = Config.MINIO_ENDPOINT.startswith("https://")

    client = Minio(
        endpoint=endpoint,
        access_key=Config.MINIO_ACCESS_KEY,
        secret_key=Config.MINIO_SECRET_KEY,
        secure=secure,
    )
    logger.info("Client MinIO initialisé", extra={"endpoint": endpoint})
    return client


def ensure_bucket_exists(client: Minio, bucket_name: str) -> None:
    """
    Crée le bucket s'il n'existe pas.

    Args:
        client: Client MinIO
        bucket_name: Nom du bucket à créer
    """
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        logger.info("Bucket créé", extra={"bucket": bucket_name})
    else:
        logger.debug("Bucket existe déjà", extra={"bucket": bucket_name})
