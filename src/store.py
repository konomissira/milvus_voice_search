import os
from typing import List, Dict, Tuple
import psycopg2
from pymilvus import Collection
from src.embed import embed_texts
from src.schemas import connect_milvus, ensure_collection, insert_embeddings, COLLECTION_NAME

def _pg_conn():
    return psycopg2.connect(
        host=os.getenv("APP_PG_HOST"),
        dbname=os.getenv("APP_PG_DB"),
        user=os.getenv("APP_PG_USER"),
        password=os.getenv("APP_PG_PASSWORD"),
    )

def _ensure_marker_table():
    with _pg_conn() as con, con.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS call_vectors_indexed (
          call_id BIGINT PRIMARY KEY,
          embedding_model_version VARCHAR(64) NOT NULL,
          indexed_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)
        con.commit()

def upsert_metadata(rows: List[Dict]) -> List[Tuple[int, str]]:
    """
    Upserts into calls and returns [(call_id, transcript), ...]
    rows: [{"external_id","file_uri","transcript"}]
    """
    out = []
    with _pg_conn() as con, con.cursor() as cur:
        for r in rows:
            cur.execute("""
              INSERT INTO calls (external_id, file_uri, transcript)
              VALUES (%s, %s, %s)
              ON CONFLICT (external_id, started_at) DO UPDATE SET transcript = EXCLUDED.transcript
              RETURNING call_id, transcript;
            """, (r["external_id"], r["file_uri"], r["transcript"]))
            cid, tx = cur.fetchone()
            out.append((cid, tx))
        con.commit()
    return out

def upsert_vectors(pairs: List[Tuple[int, str]], embed_model_version: str = "all-MiniLM-L6-v2-dim384") -> int:
    """
    pairs: [(call_id, transcript)]
    """
    if not pairs:
        return 0

    call_ids = [int(cid) for cid, _ in pairs]
    texts    = [tx for _, tx in pairs]
    vecs     = embed_texts(texts)  # normalized float32

    connect_milvus(host=os.getenv("MILVUS_HOST","127.0.0.1"), port=os.getenv("MILVUS_PORT","19530"))
    ensure_collection()
    insert_embeddings(call_ids, vecs)

    _ensure_marker_table()
    with _pg_conn() as con, con.cursor() as cur:
        cur.executemany(
            "INSERT INTO call_vectors_indexed (call_id, embedding_model_version) VALUES (%s,%s) ON CONFLICT (call_id) DO NOTHING;",
            [(cid, embed_model_version) for cid in call_ids]
        )
        con.commit()
    return len(call_ids)

def upsert_batch(rows: List[Dict]) -> int:
    """
    Convenience: upsert metadata then vectors.
    """
    pairs = upsert_metadata(rows)
    n = upsert_vectors(pairs)
    print(f"Upserted {n} vectors.")
    return n
