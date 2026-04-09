FROM apache/airflow:2.8.0-python3.11

# L'image de base inclut déjà gcc/libpq-dev/curl
# On installe directement les packages Python en tant qu'user airflow
USER airflow

# Copier et installer les dépendances Python
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --timeout=300 --retries=5 -r /tmp/requirements.txt

# S'assurer que le dossier src est dans le PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow"
