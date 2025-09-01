from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

# these import from /opt/airflow/src (PYTHONPATH set via compose)
from src.asr import transcribe_batch
from src.store import upsert_batch

from airflow.models import Variable

def _transcribe(**context):
    rows = transcribe_batch()  # [{"external_id","file_uri","transcript"}]
    context["ti"].xcom_push(key="rows", value=rows)
    return len(rows)

def _embed_and_upsert(**context):
    rows = context["ti"].xcom_pull(key="rows") or []
    from src.store import upsert_vectors, upsert_metadata  # local import to ensure PYTHONPATH ready
    pairs = upsert_metadata(rows)
    model_version = Variable.get("EMBED_MODEL_VERSION", "all-MiniLM-L6-v2-dim384")
    n = upsert_vectors(pairs, embed_model_version=model_version)
    return n

with DAG(
    dag_id="voice_semantic_dag",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,   # start manual; flip to @daily later
    catchup=False,
    tags=["etl", "asr", "milvus"],
) as dag:
    t1 = PythonOperator(task_id="transcribe", python_callable=_transcribe, provide_context=True)
    t2 = PythonOperator(task_id="embed_and_upsert", python_callable=_embed_and_upsert, provide_context=True)

    t1 >> t2
