from airflow import DAG
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
from datetime import datetime, timedelta
from airflow.models import Variable

# Récupérer les UUID depuis les variables Airflow
POSTGRES_TO_BQ = Variable.get("POSTGRES_TO_BQ")
MYSQL_TO_BQ = Variable.get("MYSQL_TO_BQ")
CMC_TO_BQ = Variable.get("CMC_TO_BQ")

default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 7, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

dag = DAG(
    "ingest_raw_data",
    default_args=default_args,
    description="Charge les données vers BigQuery depuis les bases",
    schedule_interval=None,
    catchup=False,
)

load_postgres = AirbyteTriggerSyncOperator(
    task_id="load_postgres_to_bq",
    airbyte_conn_id="airbyte_conn",
    connection_id=POSTGRES_TO_BQ,
    asynchronous=False,
    dag=dag,
)

load_mysql = AirbyteTriggerSyncOperator(
    task_id="load_mysql_to_bq",
    airbyte_conn_id="airbyte_conn",
    connection_id=MYSQL_TO_BQ,
    asynchronous=False,
    dag=dag,
)

load_api = AirbyteTriggerSyncOperator(
    task_id="load_coinmarketcap_to_bq",
    airbyte_conn_id="airbyte_conn",
    connection_id=CMC_TO_BQ,
    asynchronous=False,
    dag=dag,
)

load_postgres >> load_mysql >> load_api
