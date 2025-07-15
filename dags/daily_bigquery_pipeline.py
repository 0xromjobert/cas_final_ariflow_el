from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 7, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="daily_bigquery_pipeline",
    default_args=default_args,
    description="Orchestre la génération et l’ingestion vers BigQuery",
    schedule_interval="@daily",
    catchup=False,
) as dag:

    # Déclenche le DAG de génération avec passage explicite de l'execution_date
    trigger_generate = TriggerDagRunOperator(
        task_id="trigger_generate_data",
        trigger_dag_id="generate_transaction_and_labels",
        wait_for_completion=False,
    )

    # Déclenche le DAG d'ingestion 
    trigger_ingest = TriggerDagRunOperator(
        task_id="trigger_ingest_raw_data",
        trigger_dag_id="ingest_raw_data",
        wait_for_completion=False,
    )

    trigger_generate >> trigger_ingest
