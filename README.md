# Semaine 1 - Airflow : génération automatique des données toutes les 30 minutes

## Objectif

Remplacer le service `generator` par un pipeline planifié exécuté via un **DAG Airflow** nommé `generate_transaction_and_labels`. Ce DAG lance automatiquement deux scripts Python toutes les 30 minutes :

* `transaction_generator.py` pour générer des transactions dans PostgreSQL ;
* `detection_generator.py` pour générer des étiquettes dans MySQL.



## Structure recommandée

```
projet_final/
├── dags/
│   └── generate_data_dag.py
├── scripts/
│   ├── transaction_generator.py
│   └── detection_generator.py
├── requirements.txt
├── docker-compose.yml
└── entrypoint.sh
```

Les volumes Docker montent ces répertoires dans les conteneurs Airflow afin d’éviter le rebuild de l’image à chaque modification.



## Services Airflow requis (avec LocalExecutor)

* `webserver` : interface graphique Airflow (port 8080)
* `scheduler` : planifie et exécute les tâches du DAG
* `postgres` : base interne pour les métadonnées Airflow

Ces services sont déclarés dans un `docker-compose.yml` et partagent le réseau `airbyte_net` avec les bases de données métier (`airbyte-postgres` et `airbyte-mysql`).



## Configuration du `docker-compose.yml`

Les points clés :

* Chaque service Airflow monte les répertoires nécessaires : `dags`, `scripts`, `requirements.txt` et `entrypoint.sh`.
* Les ports doivent être évités en cas de conflit (`5432`, `3306` ou `8080`).
* Un volume distinct est utilisé pour la base PostgreSQL d’Airflow (`postgres_airflow_data`).



## Entrypoint personnalisé (`entrypoint.sh`)

Ce script est lancé dans les conteneurs `webserver` et `scheduler` pour installer les dépendances :

```bash
#!/bin/bash
set -e
pip install --no-cache-dir -r /requirements.txt

if [ "$AIRFLOW_ROLE" = "scheduler" ]; then
    airflow db init
    airflow users create \
        --username admin \
        --password admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com || true
fi

exec "$@"
```

Ne pas oublier de le rendre exécutable : `chmod +x entrypoint.sh`



## Dépendances (`requirements.txt`)

```text
psycopg2-binary
mysql-connector-python
```

Ces paquets permettent aux scripts Python de se connecter aux bases PostgreSQL et MySQL.



## Définition du DAG (`dags/generate_data_dag.py`)

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

dag = DAG(
    "generate_transaction_and_labels",
    default_args=default_args,
    description="Génère des données toutes les 30 minutes",
    schedule_interval="*/30 * * * *",
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
```

**Explications clés :**

| Élément                            | Rôle                                                                            |
| - | - |
| `BashOperator`                     | Exécute les scripts Python comme commandes shell                                |
| `schedule_interval="*/30 * * * *"` | Exécute le DAG toutes les 30 minutes                                            |
| `catchup=False`                    | Ne relance pas les exécutions passées                                           |
| `>>`                               | Dépendance : la tâche `generate_labels` s’exécute après `generate_transactions` |



## Chemins attendus dans les conteneurs

* Scripts Python montés dans `/opt/airflow/scripts`
* DAGs dans `/opt/airflow/dags`
* Les connexions aux bases utilisent les noms de services dans Docker :

```python
postgres_conn_params = {
    "host": "airbyte-postgres",
    "database": "airbyte",
    "user": "docker",
    "password": "docker"
}

mysql_conn_params = {
    "host": "airbyte-mysql",
    "database": "data",
    "user": "docker",
    "password": "docker"
}
```



## Commandes utiles

### Lancer l’environnement

```bash
docker compose down -v
docker volume prune -f
docker compose up --build
```

### Vérifier que les bases sont vides

PostgreSQL :

```bash
docker exec -it airbyte-postgres psql -U docker -d airbyte -c '\dt'
```

MySQL :

```bash
docker exec -it airbyte-mysql mysql -udocker -pdocker -e 'SHOW TABLES IN data;'
```



## Accès et interface

* Interface Airflow : [http://localhost:8080](http://localhost:8080)
* Utilisateur par défaut :

  * login : `admin`
  * mot de passe : `admin`

Dans l’interface, vous pouvez :

1. Activer le DAG `generate_transaction_and_labels`
2. Le lancer manuellement avec le bouton **Trigger DAG**
3. Suivre son exécution et inspecter les logs


## Résultat attendu

À chaque exécution (toutes les 30 minutes) :

* 50 à 200 transactions aléatoires sont insérées dans `airbyte-postgres`
* Des étiquettes de fraude sont générées dans `airbyte-mysql`


* Ajouter des alertes ou des logs personnalisés dans les scripts
* Utiliser `PythonOperator` au lieu de `BashOperator`
* Connecter les bases Airbyte dans Airflow via la section **Admin > Connections** si nécessaire pour des futurs usages


