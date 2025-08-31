from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

def say_hello():
    print("Hello from Airflow! DAG is running correctly.")

with DAG(
    dag_id="hello_world",
    start_date=datetime(2025, 1, 1),   # static start date
    schedule_interval="@daily",        # run once per day
    catchup=False,                     # don't backfill old runs
    tags=["sanity-check"],
) as dag:
    
    hello_task = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello
    )
