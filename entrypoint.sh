#!/bin/bash
set -e

# Install extra Python dependencies
pip install --no-cache-dir -r /requirements.txt

if [ "$AIRFLOW_ROLE" = "scheduler" ]; then
    echo "Initialisation de la base Airflow..."
    airflow db init

    echo "Création de l'utilisateur admin (si inexistant)..."
    airflow users create \
        --username admin \
        --password admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com || true
fi

# Exécute la commande finale passée par docker-compose
exec "$@"
