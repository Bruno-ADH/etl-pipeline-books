# Guide Utilisateur

## Flux de données

```
Extraction → Bronze → Silver → Gold → Power BI
```

Chaque étape produit des fichiers Parquet dans un bucket MinIO dédié.

## Accéder aux données dans MinIO

1. Ouvrir http://localhost:9001
2. Se connecter avec `minioadmin` / `minioadmin123`
3. Naviguer dans les buckets :
   - `bronze/` → données brutes
   - `silver/` → données nettoyées
   - `gold/` → KPIs prêts pour Power BI

## Connecter Power BI au Gold Layer

1. Dans Power BI Desktop → **Obtenir les données → Parquet**
2. URL du fichier : `http://localhost:9000/gold/<chemin>.parquet`
   - Ou télécharger le fichier depuis la console MinIO
3. Tables disponibles dans Gold :
   - `books_by_category` — KPIs par catégorie
   - `books_top_rated` — Top 20 livres
   - `books_price_distribution` — Distribution des prix
   - `weather_daily` — Météo journalière par ville
   - `weather_city_summary` — Résumé par ville

## Monitorer les DAGs

Dans l'interface Airflow (http://localhost:8080) :
- **Graph View** : visualiser les dépendances entre tâches
- **Logs** : cliquer sur une tâche → View Logs
- **Retry** : cliquer sur une tâche échouée → Clear pour relancer

## Modifier la configuration

Tous les paramètres ajustables sont dans `config/pipeline_config.yaml` :
- Ajouter/retirer des villes météo
- Changer le nombre de pages scrappées
- Ajuster les seuils de validation
