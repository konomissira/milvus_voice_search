from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
import psycopg2

def query_postgres():
    # Read env vars inside the task
    host = os.getenv("APP_PG_HOST")
    db = os.getenv("APP_PG_DB")
    user = os.getenv("APP_PG_USER")
    pwd = os.getenv("APP_PG_PASSWORD")

    if not pwd:
        raise ValueError("APP_PG_PASSWORD is not set in the Airflow environment")

    print(f"Connecting to Postgres host={host} db={db} user={user}")

    with psycopg2.connect(host=host, dbname=db, user=user, password=pwd) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT NOW();")
            now = cur.fetchone()[0]
            print(f"Connected to Postgres! Current time: {now}")

with DAG(
    dag_id="test_postgres_connection",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["sanity-check", "postgres"],
) as dag:
    PythonOperator(
        task_id="run_postgres_query",
        python_callable=query_postgres,
    )
