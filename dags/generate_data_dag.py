# dags/generate_data_dag.py

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 7, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

dag = DAG(
    "generate_transaction_and_labels",
    default_args=default_args,
    description="Génère des données toutes les 30 minutes",
    schedule_interval=None,
    catchup=False,
)

generate_transactions = BashOperator(
    task_id="generate_transactions",
    bash_command="python /opt/airflow/scripts/transaction_generator.py",
    dag=dag,
)

generate_labels = BashOperator(
    task_id="generate_labels",
    bash_command="python /opt/airflow/scripts/detection_generator.py",
    dag=dag,
)

generate_transactions >> generate_labels
