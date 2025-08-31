import os
import psycopg2
from embed import get_embedding
from schemas import connect_milvus, ensure_collection, insert_embeddings, COLLECTION_NAME
from pymilvus import Collection

def fetch_calls(limit=1):
    # Fetch some rows from Postgres calls table.
    host = os.getenv("APP_PG_HOST")
    db = os.getenv("APP_PG_DB")
    user = os.getenv("APP_PG_USER")
    pwd = os.getenv("APP_PG_PASSWORD")

    conn = psycopg2.connect(host=host, dbname=db, user=user, password=pwd)
    cur = conn.cursor()
    cur.execute("SELECT call_id, transcript FROM calls LIMIT %s;", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def main():
    # 1. Connect to Milvus & ensure collection
    connect_milvus()
    collection = ensure_collection()

    # 2. Fetch one row from Postgres
    rows = fetch_calls(limit=1)
    if not rows:
        print("⚠️ No rows in Postgres.calls table to embed.")
        return
    call_id, transcript = rows[0]
    print(f"Fetched call_id={call_id}, transcript={transcript}")

    # 3. Generate embedding
    vec = get_embedding(transcript)
    print(f"Generated embedding of length {len(vec)}")

    # 4. Insert into Milvus
    insert_embeddings([call_id], [vec])

    # 5. Verify
    collection.load()
    search_res = collection.search(
        data=[vec],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 10}},
        limit=1,
    )
    print("🔍 Search result:", search_res[0][0].id, "score:", search_res[0][0].score)

if __name__ == "__main__":
    main()
