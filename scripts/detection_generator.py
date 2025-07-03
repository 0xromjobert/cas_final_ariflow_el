# detection_generator.py
import mysql.connector
import psycopg2
from datetime import datetime
import random

# Connexions
postgres_conn_params = {
    "host": "airbyte-postgres",
    "database": "airbyte",
    "user": "docker",
    "password": "docker"
}

mysql_conn_params = {
    "host": "mysql",
    "database": "data",
    "user": "docker",
    "password": "docker"
}

def fetch_transaction_ids(data_interval_start):
    """
    Récupère les transaction_id du jour.
    """
    today = (data_interval_start or datetime.now()).strftime('%Y-%m-%d')
    query = """
    SELECT transaction_id FROM customer_transactions
    WHERE transaction_date >= %s AND transaction_date < %s::date + interval '1 day'
    ORDER BY transaction_id;
    """
    with psycopg2.connect(**postgres_conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (today, today))
            return [row[0] for row in cur.fetchall()]

def insert_labeled_transactions(transaction_ids):
    """
    Insère les flags de fraude dans MySQL.
    """
    create_query = """
    CREATE TABLE IF NOT EXISTS labeled_transactions (
        transaction_id INT PRIMARY KEY,
        is_fraudulent BOOLEAN NOT NULL
    );
    """
    insert_query = "INSERT INTO labeled_transactions (transaction_id, is_fraudulent) VALUES (%s, %s)"

    with mysql.connector.connect(**mysql_conn_params) as conn:
        cur = conn.cursor()
        cur.execute(create_query)
        for tx_id in transaction_ids:
            cur.execute(insert_query, (tx_id, random.choice([True, False])))
        conn.commit()
        cur.close()
        print("Étiquettes insérées avec succès.")

def main(data_interval_start=None):
    tx_ids = fetch_transaction_ids(data_interval_start)
    if tx_ids:
        insert_labeled_transactions(tx_ids)
    else:
        print("Aucune transaction à étiqueter pour aujourd'hui.")

if __name__ == "__main__":
    main()
