# Guide d'installation

## Prérequis

- **Docker Desktop** pour Windows — [télécharger ici](https://www.docker.com/products/docker-desktop/)
- **Python 3.11+** — pour les tests locaux
- **Git**

## Installation pas à pas

### 1. Cloner le dépôt
```bash
git clone <url-du-repo>
cd etl-pipeline-books
```

### 2. Initialiser le projet
```bash
bash scripts/init_project.sh
```
Ce script :
- Crée le fichier `.env` depuis `.env.example`
- Génère automatiquement la Fernet Key Airflow
- Vérifie la présence du fichier `Books.csv`

### 3. Placer le fichier Books.csv
Copiez votre fichier `Books.csv` à la racine du projet :
```
etl-pipeline-books/
└── Books.csv   ← ici
```

### 4. Lancer l'infrastructure Docker
```bash
bash scripts/start_pipeline.sh
```
Ou manuellement :
```bash
cd docker
docker-compose up -d
```

### 5. Attendre le démarrage (~2 minutes)
Vérifier que tout est vert :
```bash
docker-compose ps
```

### 6. Accéder aux interfaces
| Service | URL | Identifiants |
|---------|-----|--------------|
| Airflow | http://localhost:8080 | admin / admin123 |
| MinIO | http://localhost:9001 | minioadmin / minioadmin123 |

## Lancer le pipeline

### Via Airflow UI
1. Ouvrir http://localhost:8080
2. Aller dans **DAGs**
3. Activer le DAG `master_pipeline`
4. Cliquer **Trigger DAG** pour un lancement immédiat

### Via ligne de commande
```bash
docker exec -it <airflow-webserver-container> airflow dags trigger master_pipeline
```

## Lancer les tests locaux

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer tous les tests avec couverture
pytest

# Rapport HTML de couverture
open htmlcov/index.html
```

## Arrêter / Nettoyer

```bash
# Arrêter sans supprimer les données
cd docker && docker-compose stop

# Arrêt complet + suppression des volumes
bash scripts/cleanup.sh
```

## Dépannage

**Airflow ne démarre pas :**
```bash
docker-compose logs airflow-webserver
```

**MinIO inaccessible :**
```bash
docker-compose logs minio
```

**Erreur Fernet Key :**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copiez la valeur dans AIRFLOW__CORE__FERNET_KEY dans .env
```
