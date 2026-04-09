"""
DAG : Extraction Web Scraping — books.toscrape.com
Fréquence : Quotidien à 02h00 UTC
Couche cible : Bronze
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Paramètres par défaut pour toutes les tâches du DAG
default_args = {
    "owner": "etl-pipeline",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


def extract_books(**context):
    """
    Tâche principale : scrape books.toscrape.com et sauvegarde en Bronze.
    """
    from src.extractors.web_scraper import BookScraper
    from src.loaders.minio_loader import MinIOLoader
    from src.utils.logger import get_logger

    logger = get_logger("dag.extract_books")
    logger.info("Démarrage extraction livres web", extra={"dag_run": context["run_id"]})

    # Extraction
    scraper = BookScraper()
    df = scraper.scrape()

    if df.empty:
        raise ValueError("Aucun livre extrait — annulation du DAG")

    # Chargement en Bronze
    loader = MinIOLoader()
    path = loader.save(df, source="books_web", layer="bronze")

    logger.info("Extraction terminée", extra={"rows": len(df), "path": path})

    # Passer le chemin à la tâche suivante via XCom
    return path


with DAG(
    dag_id="extract_books_web",
    description="Scrape books.toscrape.com → Bronze Layer",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="0 2 * * *",  # Tous les jours à 02h00 UTC
    catchup=False,
    tags=["extract", "bronze", "books", "web-scraping"],
) as dag:

    task_extract = PythonOperator(
        task_id="scrape_books_to_bronze",
        python_callable=extract_books,
    )
