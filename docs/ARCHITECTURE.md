# Architecture du Pipeline ETL

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOURCES DE DONNÉES                        │
│  ┌──────────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ books.toscrape   │  │  Books.csv   │  │  Open-Meteo API   │  │
│  │  (web scraping)  │  │   (fichier)  │  │  (météo 5 villes) │  │
│  └────────┬─────────┘  └──────┬───────┘  └────────┬──────────┘  │
└───────────┼───────────────────┼───────────────────┼─────────────┘
            │                   │                   │
            ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BRONZE LAYER (MinIO)                         │
│              Données brutes en Parquet, partitionnées            │
│         bronze/books_web/YYYY/MM/DD/  · books_csv/ · weather/   │
└─────────────────────────────┬───────────────────────────────────┘
                              │  BronzeCleaner (Pandas)
                              │  - Déduplication
                              │  - Validation types
                              │  - Suppression aberrants
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SILVER LAYER (MinIO)                         │
│                    Données nettoyées en Parquet                  │
│         silver/books_web/ · books_csv/ · weather/               │
└─────────────────────────────┬───────────────────────────────────┘
                              │  SilverAggregator (Pandas)
                              │  - Agrégations par catégorie
                              │  - KPIs, statistiques
                              │  - Jointures
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GOLD LAYER (MinIO)                          │
│                  Données agrégées prêtes pour BI                 │
│  books_by_category · books_top_rated · weather_daily · ...      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
                        ┌──────────┐
                        │ Power BI │
                        └──────────┘
```

## Orchestration Airflow

| DAG | Rôle | Schedule |
|-----|------|----------|
| `extract_books_web` | Scrape books.toscrape.com → Bronze | Quotidien 02h00 |
| `extract_books_csv` | Lit Books.csv → Bronze | Hebdomadaire |
| `extract_weather_api` | Open-Meteo 5 villes → Bronze | Toutes les heures |
| `bronze_to_silver` | Nettoyage Bronze → Silver | Quotidien 04h00 |
| `silver_to_gold` | Agrégations Silver → Gold | Quotidien 06h00 |
| `master_pipeline` | Orchestration complète | Quotidien 01h00 |

## Stack Technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Orchestration | Apache Airflow | 2.8.0 |
| Traitement | Pandas + PyArrow | 2.1.4 |
| Stockage | MinIO (S3) | latest |
| Sérialisation | Parquet (Snappy) | — |
| Messagerie | Redis (Celery) | 7 |
| Metadata | PostgreSQL | 15 |
| Conteneurs | Docker Compose | v3.8 |
| Web scraping | BeautifulSoup4 | 4.12 |
| HTTP | httpx + tenacity | — |

## Structure des données

### Bronze — books_web (Parquet)
| Colonne | Type | Description |
|---------|------|-------------|
| title | string | Titre du livre |
| price | float | Prix en £ |
| rating | int | Étoiles (1-5) |
| category | string | Catégorie |
| in_stock | bool | Disponibilité |
| extracted_at | string | Timestamp extraction |

### Gold — books_by_category (Parquet)
| Colonne | Type | Description |
|---------|------|-------------|
| category | string | Catégorie |
| nb_books | int | Nombre de livres |
| avg_price | float | Prix moyen |
| avg_rating | float | Rating moyen |
| stock_rate | float | % en stock |
