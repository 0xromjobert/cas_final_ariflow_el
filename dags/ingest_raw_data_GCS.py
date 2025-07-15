from airflow import DAG
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable
from datetime import datetime, timedelta

# Récupération des UUID des connexions depuis les variables Airflow
PG_TO_GCS = Variable.get("POSTGRES_TO_GCS")
MYSQL_TO_GCS = Variable.get("MYSQL_TO_GCS")
CMC_TO_GCS = Variable.get("CMC_TO_GCS")

GCS_TO_BQ_TRANSACTIONS = Variable.get("GCS_TRANSACTIONS_TO_BQ")
GCS_TO_BQ_LABELS = Variable.get("GCS_LABELS_TO_BQ")
GCS_TO_BQ_CMC = Variable.get("GCS_CMC_TO_BQ")

default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 7, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    "ingest_raw_data_GCS",
    default_args=default_args,
    description="Ingestion complète des données depuis GCS vers BigQuery après extraction des sources",
    schedule_interval=None,  # Ce DAG est déclenché par un DAG parent
    catchup=False,
    tags=["airbyte", "orchestration", "gcs", "bigquery"],
) as dag:

    # Étape 1 : sources → GCS
    extract_pg = AirbyteTriggerSyncOperator(
        task_id="extract_postgres_to_gcs",
        airbyte_conn_id="airbyte_conn",
        connection_id=PG_TO_GCS,
    )

    extract_mysql = AirbyteTriggerSyncOperator(
        task_id="extract_mysql_to_gcs",
        airbyte_conn_id="airbyte_conn",
        connection_id=MYSQL_TO_GCS,
    )

    extract_cmc = AirbyteTriggerSyncOperator(
        task_id="extract_cmc_to_gcs",
        airbyte_conn_id="airbyte_conn",
        connection_id=CMC_TO_GCS,
    )

    # Cette tâche est un point de synchronisation pour s'assurer que toutes les extractions vers GCS sont terminées
    all_gcs_ingested = EmptyOperator(task_id="all_gcs_ingested")
    

    # Étape 2 : GCS → BigQuery
    load_transactions = AirbyteTriggerSyncOperator(
        task_id="load_gcs_transactions_to_bq",
        airbyte_conn_id="airbyte_conn",
        connection_id=GCS_TO_BQ_TRANSACTIONS,
    )

    load_labels = AirbyteTriggerSyncOperator(
        task_id="load_gcs_labels_to_bq",
        airbyte_conn_id="airbyte_conn",
        connection_id=GCS_TO_BQ_LABELS,
    )

    load_cmc = AirbyteTriggerSyncOperator(
        task_id="load_gcs_cmc_to_bq",
        airbyte_conn_id="airbyte_conn",
        connection_id=GCS_TO_BQ_CMC,
    )

    # Dépendances : toutes les extractions doivent être terminées avant les chargements
    #[extract_pg, extract_mysql, extract_cmc] >> all_gcs_ingested >> [load_transactions, load_labels, load_cmc]

    #tache bigquery sequentielle (moins de ressources)
    [extract_pg, extract_mysql, extract_cmc] >> load_transactions >> load_labels >> load_cmc    
    
    #tout en séquentiel pour éviter les problèmes de ressources
    #extract_pg >> extract_mysql >> extract_cmc >> load_transactions >> load_labels >> load_cmc
