from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.external_task import ExternalTaskSensor
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
        conf={"forced_execution_date": "{{ ds }}"},  # ds = execution_date format YYYY-MM-DD
        wait_for_completion=False,
    )

    # Attend que la tâche generate_labels du DAG externe soit terminée avec succès
    wait_generate = ExternalTaskSensor(
        task_id="wait_generate_data",
        external_dag_id="generate_transaction_and_labels",
        external_task_id="generate_labels",
        execution_date_fn=lambda exec_date: exec_date,  # synchronisation exacte
        allowed_states=["success"],
        timeout=900,  # 15 minutes
        poke_interval=30,
        mode="poke",  # ou "reschedule" si DAG long
    )

    # Déclenche le DAG d'ingestion une fois la génération terminée
    trigger_ingest = TriggerDagRunOperator(
        task_id="trigger_ingest_raw_data",
        trigger_dag_id="ingest_raw_data",
        conf={"forced_execution_date": "{{ ds }}"},
        wait_for_completion=False,
    )

    trigger_generate >> wait_generate >> trigger_ingest
