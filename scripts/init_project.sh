#!/bin/bash
# ============================================================
# INITIALISATION DU PROJET
# À exécuter une seule fois avant le premier lancement
# ============================================================

set -e

echo "=== Initialisation du Pipeline ETL ==="

# 1. Vérifier les prérequis
echo "[1/5] Vérification des prérequis..."
command -v docker >/dev/null 2>&1 || { echo "ERREUR: Docker n'est pas installé."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "ERREUR: docker-compose n'est pas installé."; exit 1; }

# 2. Copier le .env si absent
echo "[2/5] Configuration des variables d'environnement..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ✓ .env créé depuis .env.example"
    echo "  ⚠ Vérifiez et adaptez les valeurs dans .env avant de continuer"
else
    echo "  ✓ .env déjà présent"
fi

# 3. Générer une Fernet Key Airflow si non définie
echo "[3/5] Génération de la Fernet Key Airflow..."
if grep -q "your_fernet_key_here" .env; then
    FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "PLACEHOLDER_FERNET_KEY")
    sed -i "s/your_fernet_key_here/${FERNET_KEY}/" .env
    echo "  ✓ Fernet Key générée"
fi

# 4. Copier le fichier Books.csv si nécessaire
echo "[4/5] Vérification du fichier CSV..."
if [ -f "../Books.csv" ] && [ ! -f "Books.csv" ]; then
    cp ../Books.csv ./Books.csv
    echo "  ✓ Books.csv copié"
elif [ -f "Books.csv" ]; then
    echo "  ✓ Books.csv déjà présent"
else
    echo "  ⚠ Books.csv introuvable - placez-le à la racine du projet"
fi

# 5. Créer les dossiers de logs
echo "[5/5] Création des dossiers..."
mkdir -p logs

echo ""
echo "=== Initialisation terminée ==="
echo "Lancez maintenant : ./scripts/start_pipeline.sh"
