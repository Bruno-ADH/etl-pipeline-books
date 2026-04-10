#!/bin/bash
# ============================================================
# DÉMARRAGE DU PIPELINE ETL
# ============================================================

set -e

echo "=== Démarrage du Pipeline ETL ==="

# Se positionner dans le dossier docker
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT/docker"

# Lancer tous les services en arrière-plan
echo "[1/3] Lancement des conteneurs Docker..."
docker-compose up -d

# Attendre que les services soient prêts
echo "[2/3] Attente du démarrage des services (~60s)..."
sleep 30

# Vérifier l'état des services
echo "[3/3] État des services :"
docker-compose ps

echo ""
echo "=== Pipeline démarré ==="
echo "  Airflow UI : http://localhost:8080  (admin / admin123)"
echo "  MinIO UI   : http://localhost:9001  (minioadmin / minioadmin123)"
echo ""
echo "Pour déclencher le pipeline manuellement :"
echo "  Airflow → DAGs → master_pipeline → Trigger DAG"
