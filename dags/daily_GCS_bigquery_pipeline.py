from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 7, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="daily_GCS_bigquery_pipeline",
    default_args=default_args,
    description="Pipeline principal déclenchant la génération puis l’ingestion via GCS",
    schedule_interval="@daily",  # Exécution automatique tous les jours
    catchup=False,
    tags=["pipeline", "gcs", "bigquery", "daily"],
) as dag:

    # Étape 1 : déclenchement du DAG de génération de données sources (PostgreSQL, MySQL)
    trigger_generate_data = TriggerDagRunOperator(
        task_id="trigger_generate_transaction_and_labels",
        trigger_dag_id="generate_transaction_and_labels",
        wait_for_completion=True,  # On attend que la génération soit terminée
    )

    # Étape 2 : déclenchement du DAG d’ingestion GCS → BigQuery
    trigger_ingest = TriggerDagRunOperator(
        task_id="trigger_ingest_raw_data_GCS",
        trigger_dag_id="ingest_raw_data_GCS",
        wait_for_completion=False,  # On peut exécuter le reste en asynchrone si souhaité
    )

    # Dépendance : on lance l'ingestion seulement après génération
    trigger_generate_data >> trigger_ingest
