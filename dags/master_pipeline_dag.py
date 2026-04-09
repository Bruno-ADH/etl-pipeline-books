"""
DAG Master — Orchestration complète du pipeline ETL
Lance séquentiellement :
  1. Extractions en parallèle (web + csv + météo)
  2. Nettoyage Bronze → Silver
  3. Agrégations Silver → Gold

Fréquence : Quotidien à 01h00 UTC
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.dates import days_ago

default_args = {
    "owner": "etl-pipeline",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}


def log_pipeline_start(**context):
    from src.utils.logger import get_logger
    logger = get_logger("dag.master_pipeline")
    logger.info(
        "=== PIPELINE MASTER DÉMARRÉ ===",
        extra={"run_id": context["run_id"], "execution_date": str(context["execution_date"])},
    )
    return "started"


def log_pipeline_end(**context):
    from src.utils.logger import get_logger
    logger = get_logger("dag.master_pipeline")
    logger.info(
        "=== PIPELINE MASTER TERMINÉ ===",
        extra={"run_id": context["run_id"]},
    )
    return "completed"


# Fonctions d'extraction inline (réutilisent les modules src)
def run_extract_books_web(**context):
    from src.extractors.web_scraper import BookScraper
    from src.loaders.minio_loader import MinIOLoader
    scraper = BookScraper()
    df = scraper.scrape()
    loader = MinIOLoader()
    return loader.save(df, source="books_web", layer="bronze")


def run_extract_books_csv(**context):
    from src.extractors.csv_reader import CSVReader
    from src.loaders.minio_loader import MinIOLoader
    reader = CSVReader()
    df = reader.extract()
    loader = MinIOLoader()
    return loader.save(df, source="books_csv", layer="bronze")


def run_extract_weather(**context):
    from src.extractors.weather_api import WeatherAPIExtractor
    from src.loaders.minio_loader import MinIOLoader
    extractor = WeatherAPIExtractor()
    df = extractor.extract()
    loader = MinIOLoader()
    return loader.save(df, source="weather", layer="bronze")


def run_bronze_to_silver(**context):
    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.bronze_cleaner import BronzeCleaner
    from src.utils.config import Config
    import pandas as pd

    loader = MinIOLoader()
    cleaner = BronzeCleaner()

    # Nettoyer les 3 sources
    for source, clean_fn in [
        ("books_web", cleaner.clean_books),
        ("books_csv", cleaner.clean_books),
        ("weather", cleaner.clean_weather),
    ]:
        try:
            df_raw = loader.load_latest(Config.MINIO_BUCKET_BRONZE, source)
            df_clean = clean_fn(df_raw)
            loader.save(df_clean, source=source, layer="silver")
        except FileNotFoundError:
            pass  # Source pas encore disponible, on continue


def run_silver_to_gold(**context):
    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.silver_aggregator import SilverAggregator
    from src.utils.config import Config
    import pandas as pd

    loader = MinIOLoader()
    aggregator = SilverAggregator()

    # Agrégations livres
    frames = []
    for source in ["books_web", "books_csv"]:
        try:
            frames.append(loader.load_latest(Config.MINIO_BUCKET_SILVER, source))
        except FileNotFoundError:
            pass

    if frames:
        df_books = pd.concat(frames, ignore_index=True)
        loader.save(aggregator.aggregate_books_by_category(df_books), "books_by_category", "gold")
        loader.save(aggregator.aggregate_top_rated_books(df_books), "books_top_rated", "gold")
        loader.save(aggregator.aggregate_books_price_distribution(df_books), "books_price_distribution", "gold")

    # Agrégations météo
    try:
        df_weather = loader.load_latest(Config.MINIO_BUCKET_SILVER, "weather")
        loader.save(aggregator.aggregate_weather_daily(df_weather), "weather_daily", "gold")
        loader.save(aggregator.aggregate_weather_city_summary(df_weather), "weather_city_summary", "gold")
    except FileNotFoundError:
        pass


with DAG(
    dag_id="master_pipeline",
    description="Pipeline ETL complet : Extract → Bronze → Silver → Gold",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="0 1 * * *",  # Tous les jours à 01h00 UTC
    catchup=False,
    tags=["master", "pipeline", "etl"],
) as dag:

    # Étape 0 : Log démarrage
    start = PythonOperator(
        task_id="pipeline_start",
        python_callable=log_pipeline_start,
    )

    # Étape 1 : Extractions en parallèle
    extract_web = PythonOperator(
        task_id="extract_books_web",
        python_callable=run_extract_books_web,
    )
    extract_csv = PythonOperator(
        task_id="extract_books_csv",
        python_callable=run_extract_books_csv,
    )
    extract_weather = PythonOperator(
        task_id="extract_weather",
        python_callable=run_extract_weather,
    )

    # Étape 2 : Nettoyage (attend que toutes les extractions soient terminées)
    bronze_to_silver = PythonOperator(
        task_id="bronze_to_silver",
        python_callable=run_bronze_to_silver,
    )

    # Étape 3 : Agrégations
    silver_to_gold = PythonOperator(
        task_id="silver_to_gold",
        python_callable=run_silver_to_gold,
    )

    # Étape 4 : Log fin
    end = PythonOperator(
        task_id="pipeline_end",
        python_callable=log_pipeline_end,
    )

    # Dépendances : start → [extractions en //] → bronze_to_silver → silver_to_gold → end
    start >> [extract_web, extract_csv, extract_weather] >> bronze_to_silver >> silver_to_gold >> end
