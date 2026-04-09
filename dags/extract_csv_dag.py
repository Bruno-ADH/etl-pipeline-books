"""
DAG : Extraction CSV — Books.csv
Fréquence : Déclenchement manuel (ou hebdomadaire)
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
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}


def extract_csv(**context):
    """
    Tâche principale : lit le fichier CSV et sauvegarde en Bronze.
    """
    from src.extractors.csv_reader import CSVReader
    from src.loaders.minio_loader import MinIOLoader
    from src.utils.logger import get_logger

    logger = get_logger("dag.extract_csv")
    logger.info("Démarrage extraction CSV", extra={"dag_run": context["run_id"]})

    # Extraction
    reader = CSVReader()
    df = reader.extract()

    if df.empty:
        raise ValueError("CSV vide — annulation du DAG")

    # Chargement en Bronze
    loader = MinIOLoader()
    path = loader.save(df, source="books_csv", layer="bronze")

    logger.info("Extraction CSV terminée", extra={"rows": len(df), "path": path})
    return path


with DAG(
    dag_id="extract_books_csv",
    description="Lit Books.csv → Bronze Layer",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="@weekly",
    catchup=False,
    tags=["extract", "bronze", "books", "csv"],
) as dag:

    task_extract = PythonOperator(
        task_id="read_csv_to_bronze",
        python_callable=extract_csv,
    )
