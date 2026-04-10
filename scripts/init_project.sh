#!/bin/bash
# ============================================================
# INITIALISATION DU PROJET
# À exécuter une seule fois avant le premier lancement
# ============================================================

set -e

echo "=== Initialisation du Pipeline ETL ==="

# 1. Vérifier les prérequis
echo "[1/3] Vérification des prérequis..."
command -v docker >/dev/null 2>&1 || { echo "ERREUR: Docker n'est pas installé."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "ERREUR: docker-compose n'est pas installé."; exit 1; }

# 2. Vérifier le fichier Books.csv
echo "[2/3] Vérification du fichier CSV..."
if [ -f "Books.csv" ]; then
    echo "  ✓ Books.csv présent"
else
    echo "  ⚠ Books.csv introuvable - vérifiez que le repo a été cloné correctement"
fi

# 3. Créer les dossiers de logs
echo "[3/3] Création des dossiers..."
mkdir -p logs

echo ""
echo "=== Initialisation terminée ==="
echo "Lancez maintenant : ./scripts/start_pipeline.sh"
