"""
DAG : Transformation Bronze → Silver
Nettoyage et validation de toutes les sources.
Fréquence : Quotidien à 04h00 UTC (après les extractions)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "etl-pipeline",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def clean_books_web(**context):
    """Nettoie les données livres issues du web scraper."""
    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.bronze_cleaner import BronzeCleaner
    from src.utils.config import Config
    from src.utils.logger import get_logger

    logger = get_logger("dag.bronze_to_silver.books_web")
    loader = MinIOLoader()
    cleaner = BronzeCleaner()

    df_raw = loader.load_latest(Config.MINIO_BUCKET_BRONZE, "books_web")
    df_clean = cleaner.clean_books(df_raw)
    path = loader.save(df_clean, source="books_web", layer="silver")

    logger.info("Books web nettoyés", extra={"rows": len(df_clean), "path": path})
    return path


def clean_books_csv(**context):
    """Nettoie les données livres issues du CSV."""
    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.bronze_cleaner import BronzeCleaner
    from src.utils.config import Config
    from src.utils.logger import get_logger

    logger = get_logger("dag.bronze_to_silver.books_csv")
    loader = MinIOLoader()
    cleaner = BronzeCleaner()

    df_raw = loader.load_latest(Config.MINIO_BUCKET_BRONZE, "books_csv")
    df_clean = cleaner.clean_books(df_raw)
    path = loader.save(df_clean, source="books_csv", layer="silver")

    logger.info("Books CSV nettoyés", extra={"rows": len(df_clean), "path": path})
    return path


def clean_weather(**context):
    """Nettoie les données météo."""
    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.bronze_cleaner import BronzeCleaner
    from src.utils.config import Config
    from src.utils.logger import get_logger

    logger = get_logger("dag.bronze_to_silver.weather")
    loader = MinIOLoader()
    cleaner = BronzeCleaner()

    df_raw = loader.load_latest(Config.MINIO_BUCKET_BRONZE, "weather")
    df_clean = cleaner.clean_weather(df_raw)
    path = loader.save(df_clean, source="weather", layer="silver")

    logger.info("Météo nettoyée", extra={"rows": len(df_clean), "path": path})
    return path


with DAG(
    dag_id="bronze_to_silver",
    description="Nettoyage Bronze → Silver (livres + météo)",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="0 4 * * *",  # Tous les jours à 04h00 UTC
    catchup=False,
    tags=["transform", "silver", "bronze"],
) as dag:

    task_books_web = PythonOperator(
        task_id="clean_books_web",
        python_callable=clean_books_web,
    )

    task_books_csv = PythonOperator(
        task_id="clean_books_csv",
        python_callable=clean_books_csv,
    )

    task_weather = PythonOperator(
        task_id="clean_weather",
        python_callable=clean_weather,
    )

    # Les 3 tâches tournent en parallèle
    [task_books_web, task_books_csv, task_weather]
