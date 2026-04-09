"""
DAG : Extraction API Open-Meteo — données météo
Fréquence : Toutes les heures
Couche cible : Bronze
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "etl-pipeline",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


def extract_weather(**context):
    """
    Tâche principale : appelle Open-Meteo pour toutes les villes et sauvegarde en Bronze.
    """
    from src.extractors.weather_api import WeatherAPIExtractor
    from src.loaders.minio_loader import MinIOLoader
    from src.utils.logger import get_logger

    logger = get_logger("dag.extract_weather")
    logger.info("Démarrage extraction météo", extra={"dag_run": context["run_id"]})

    # Extraction
    extractor = WeatherAPIExtractor()
    df = extractor.extract()

    if df.empty:
        raise ValueError("Aucune donnée météo extraite — annulation")

    # Chargement en Bronze
    loader = MinIOLoader()
    path = loader.save(df, source="weather", layer="bronze")

    logger.info(
        "Extraction météo terminée",
        extra={"rows": len(df), "path": path},
    )
    return path


with DAG(
    dag_id="extract_weather_api",
    description="Open-Meteo API → Bronze Layer (5 villes, toutes les heures)",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="@hourly",
    catchup=False,
    tags=["extract", "bronze", "weather", "api"],
) as dag:

    task_extract = PythonOperator(
        task_id="fetch_weather_to_bronze",
        python_callable=extract_weather,
    )
