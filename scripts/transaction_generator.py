# transaction_generator.py
import psycopg2
from psycopg2 import sql
import random
from datetime import datetime, timedelta

# Connexion PostgreSQL
conn_params = {
    "host": "airbyte-postgres",  # Changez ceci si nécessaire
    "port": 5432, 
    "database": "airbyte",
    "user": "docker",
    "password": "docker"
}

STOCK_SYMBOLS = ["AAPL", "TSLA", "GOOGL", "AMZN", "MSFT", "OR.PA", "BNP.PA", "AIR.PA"]

def create_transactions_table():
    """
    Crée la table customer_transactions si elle n'existe pas.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS customer_transactions (
        transaction_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        transaction_date TIMESTAMP NOT NULL,
        amount DECIMAL(10, 2) NOT NULL,
        stock_symbol TEXT NOT NULL
    );
    """
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            conn.commit()

def generate_transaction_data(user_id, num_transactions, data_interval_start):
    """
    Génère des transactions avec symboles boursiers aléatoires.
    """
    transactions = []
    for _ in range(num_transactions):
        date = (
            data_interval_start + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            if data_interval_start else
            datetime.now() - timedelta(hours=random.randint(1, 23), minutes=random.randint(0, 59))
        )
        amount = round(random.uniform(5.0, 500.0), 2)
        symbol = random.choice(STOCK_SYMBOLS)
        transactions.append((user_id, date, amount, symbol))
    return transactions

def insert_transactions_into_db(transactions):
    """
    Insère les transactions dans PostgreSQL.
    """
    insert_query = sql.SQL(
        "INSERT INTO customer_transactions (user_id, transaction_date, amount, stock_symbol) VALUES (%s, %s, %s, %s)"
    )
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_query, transactions)
            conn.commit()

def main(data_interval_start=None):
    create_transactions_table()
    for user_id in range(1, 11):
        tx = generate_transaction_data(user_id, random.randint(5, 20), data_interval_start)
        insert_transactions_into_db(tx)
    print("Transactions générées avec succès.")

if __name__ == "__main__":
    main()
