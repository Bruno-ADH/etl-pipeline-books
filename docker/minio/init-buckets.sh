#!/bin/sh
# ============================================================
# INITIALISATION DES BUCKETS MINIO
# Crée les buckets bronze, silver et gold au premier démarrage
# ============================================================

echo "Attente que MinIO soit prêt..."
sleep 5

# Configurer le client mc pour pointer vers MinIO
mc alias set local http://minio:9000 ${MINIO_ROOT_USER:-minioadmin} ${MINIO_ROOT_PASSWORD:-minioadmin123}

# Créer les buckets s'ils n'existent pas
for bucket in bronze silver gold; do
    if mc ls local/$bucket > /dev/null 2>&1; then
        echo "Bucket '$bucket' existe déjà."
    else
        mc mb local/$bucket
        echo "Bucket '$bucket' créé avec succès."
    fi
done

# Politique d'accès en lecture publique (optionnel, pour faciliter le dev)
# mc anonymous set public local/gold

echo "Initialisation MinIO terminée."
