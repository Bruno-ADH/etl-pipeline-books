"""
DAG : Agregation Silver vers Gold
Produit les KPIs et statistiques pour Power BI.
Frequence : Quotidien a 06h00 UTC.
"""

from datetime import timedelta

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


def aggregate_books_categories(**context):
    """Agrege les livres par categorie."""
    import pandas as pd

    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.silver_aggregator import SilverAggregator
    from src.utils.config import Config
    from src.utils.logger import get_logger

    logger = get_logger("dag.silver_to_gold.categories")
    loader = MinIOLoader()
    aggregator = SilverAggregator()

    frames = []
    for source in ["books_web", "books_csv"]:
        try:
            df = loader.load_latest(Config.MINIO_BUCKET_SILVER, source)
            frames.append(df)
        except FileNotFoundError:
            logger.warning(f"Source {source} introuvable en Silver, ignoree")

    if not frames:
        raise ValueError("Aucune donnee livres en Silver")

    df_books = pd.concat(frames, ignore_index=True)
    df_agg = aggregator.aggregate_books_by_category(df_books)
    path = loader.save(df_agg, source="books_by_category", layer="gold")

    logger.info("Agregation categories terminee", extra={"path": path})
    return path


def aggregate_books_top_rated(**context):
    """Produit le top 20 des livres les mieux notes."""
    import pandas as pd

    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.silver_aggregator import SilverAggregator
    from src.utils.config import Config
    from src.utils.logger import get_logger

    logger = get_logger("dag.silver_to_gold.top_rated")
    loader = MinIOLoader()
    aggregator = SilverAggregator()

    frames = []
    for source in ["books_web", "books_csv"]:
        try:
            frames.append(loader.load_latest(Config.MINIO_BUCKET_SILVER, source))
        except FileNotFoundError:
            pass

    if not frames:
        raise ValueError("Aucune donnee livres en Silver")

    df_books = pd.concat(frames, ignore_index=True)
    df_top = aggregator.aggregate_top_rated_books(df_books, top_n=20)
    path = loader.save(df_top, source="books_top_rated", layer="gold")

    logger.info("Top livres calcule", extra={"path": path})
    return path


def aggregate_books_price_dist(**context):
    """Distribution des prix des livres."""
    import pandas as pd

    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.silver_aggregator import SilverAggregator
    from src.utils.config import Config
    from src.utils.logger import get_logger

    logger = get_logger("dag.silver_to_gold.price_dist")
    loader = MinIOLoader()
    aggregator = SilverAggregator()

    frames = []
    for source in ["books_web", "books_csv"]:
        try:
            frames.append(loader.load_latest(Config.MINIO_BUCKET_SILVER, source))
        except FileNotFoundError:
            pass

    if not frames:
        raise ValueError("Aucune donnee livres en Silver")

    df_books = pd.concat(frames, ignore_index=True)
    df_dist = aggregator.aggregate_books_price_distribution(df_books)
    path = loader.save(df_dist, source="books_price_distribution", layer="gold")

    logger.info("Distribution prix calculee", extra={"path": path})
    return path


def aggregate_weather_daily(**context):
    """Statistiques meteo journalieres par ville."""
    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.silver_aggregator import SilverAggregator
    from src.utils.config import Config
    from src.utils.logger import get_logger

    logger = get_logger("dag.silver_to_gold.weather_daily")
    loader = MinIOLoader()
    aggregator = SilverAggregator()

    df_weather = loader.load_latest(Config.MINIO_BUCKET_SILVER, "weather")
    df_agg = aggregator.aggregate_weather_daily(df_weather)
    path = loader.save(df_agg, source="weather_daily", layer="gold")

    logger.info("Meteo journaliere agregée", extra={"path": path})
    return path


def aggregate_weather_city_summary(**context):
    """Resume meteo global par ville."""
    from src.loaders.minio_loader import MinIOLoader
    from src.transformers.silver_aggregator import SilverAggregator
    from src.utils.config import Config
    from src.utils.logger import get_logger

    logger = get_logger("dag.silver_to_gold.weather_city_summary")
    loader = MinIOLoader()
    aggregator = SilverAggregator()

    df_weather = loader.load_latest(Config.MINIO_BUCKET_SILVER, "weather")
    df_agg = aggregator.aggregate_weather_city_summary(df_weather)
    path = loader.save(df_agg, source="weather_city_summary", layer="gold")

    logger.info("Resume meteo agrege", extra={"path": path})
    return path


with DAG(
    dag_id="silver_to_gold",
    description="Agregations Silver vers Gold (KPIs pour Power BI)",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="0 6 * * *",
    catchup=False,
    tags=["transform", "gold", "silver", "kpi"],
) as dag:

    task_categories = PythonOperator(
        task_id="aggregate_books_categories",
        python_callable=aggregate_books_categories,
    )

    task_top_rated = PythonOperator(
        task_id="aggregate_books_top_rated",
        python_callable=aggregate_books_top_rated,
    )

    task_price_dist = PythonOperator(
        task_id="aggregate_books_price_distribution",
        python_callable=aggregate_books_price_dist,
    )

    task_weather = PythonOperator(
        task_id="aggregate_weather_daily",
        python_callable=aggregate_weather_daily,
    )

    task_weather_summary = PythonOperator(
        task_id="aggregate_weather_city_summary",
        python_callable=aggregate_weather_city_summary,
    )

    [task_categories, task_top_rated, task_price_dist, task_weather, task_weather_summary]
