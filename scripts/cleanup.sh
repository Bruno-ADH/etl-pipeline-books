#!/bin/bash
# ============================================================
# NETTOYAGE DE L'ENVIRONNEMENT
# Arrête les conteneurs et supprime les volumes (données incluses)
# ATTENTION : supprime toutes les données MinIO et PostgreSQL
# ============================================================

echo "=== Nettoyage du Pipeline ETL ==="
echo "⚠ ATTENTION : Cette opération supprime tous les volumes Docker (données MinIO + PostgreSQL)"
read -p "Continuer ? (o/N) : " confirm

if [[ "$confirm" != "o" && "$confirm" != "O" ]]; then
    echo "Annulé."
    exit 0
fi

cd "$(dirname "$0")/../docker"

echo "[1/2] Arrêt et suppression des conteneurs..."
docker-compose down -v

echo "[2/2] Suppression des logs Airflow..."
rm -rf ../logs/*

echo ""
echo "=== Nettoyage terminé ==="
