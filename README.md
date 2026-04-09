# Pipeline ETL Industrialisé — AfricaTechUp

Pipeline ETL complet avec architecture Medallion (Bronze / Silver / Gold), orchestré par Apache Airflow et stocké dans MinIO.

## Sources de données
| Source | Description | Fréquence |
|--------|-------------|-----------|
| books.toscrape.com | Web scraping livres (titre, prix, catégorie, rating, stock) | Quotidien |
| Books.csv | Fichier CSV de métadonnées livres | À la demande |
| Open-Meteo API | Météo temps réel pour plusieurs villes | Toutes les heures |

## Architecture
```
Sources → Bronze Layer (brut) → Silver Layer (nettoyé) → Gold Layer (agrégé) → Power BI
```
Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) pour le détail.

## Prérequis
- Docker Desktop (Windows)
- Python 3.11+
- Git

## Démarrage rapide
```bash
# 1. Cloner et configurer
git clone <repo-url>
cd etl-pipeline-books
cp .env.example .env

# 2. Lancer l'infrastructure
cd docker
docker-compose up -d

# 3. Attendre ~2 minutes, puis ouvrir :
#    Airflow : http://localhost:8080  (admin / admin123)
#    MinIO   : http://localhost:9001  (minioadmin / minioadmin123)
```

Voir [docs/SETUP.md](docs/SETUP.md) pour les instructions détaillées.

## Lancer les tests
```bash
pip install -r requirements.txt
pytest
```
