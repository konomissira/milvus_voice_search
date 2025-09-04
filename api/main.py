from typing import List, Dict, Any, Optional
import os
import psycopg2
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pymilvus import connections, Collection
from src.embed import get_embedding  # re-use the existing helper

from fastapi import HTTPException

MILVUS_HOST = os.getenv("MILVUS_HOST", "127.0.0.1")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = os.getenv("MILVUS_COLLECTION", "call_embeddings")

PG_HOST = os.getenv("APP_PG_HOST", "localhost")
PG_DB = os.getenv("APP_PG_DB", "voice")
PG_USER = os.getenv("APP_PG_USER", "postgres")
PG_PASSWORD = os.getenv("APP_PG_PASSWORD")

app = FastAPI(title="Voice Search API", version="1.0.0")

# Allow local dev tools (Swagger/localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

def _pg_conn():
    return psycopg2.connect(
        host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )

def _fetch_metadata(call_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    # Fetch metadata for given call_ids from Postgres.
    if not call_ids:
        return {}
    q = """
      SELECT call_id, external_id, customer_id, started_at, duration_sec, file_uri, summary, sentiment
      FROM calls
      WHERE call_id = ANY(%s)
    """
    with _pg_conn() as con, con.cursor() as cur:
        cur.execute(q, (call_ids,))
        rows = cur.fetchall()
    meta = {}
    for r in rows:
        (cid, external_id, customer_id, started_at, duration_sec, file_uri, summary, sentiment) = r
        meta[int(cid)] = {
            "external_id": external_id,
            "customer_id": customer_id,
            "started_at": started_at.isoformat() if started_at else None,
            "duration_sec": duration_sec,
            "file_uri": file_uri,
            "summary": summary,
            "sentiment": sentiment,
        }
    return meta

@app.on_event("startup")
def _startup():
    # Milvus connection once at startup
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)

@app.get("/search-min")
def search_min(query: str, top_k: int = 5):
    try:
        # 1) Embed the query
        qvec = get_embedding(query)

        # 2) Milvus search
        col = Collection(COLLECTION_NAME)
        col.load()
        res = col.search(
            data=[qvec],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=[],
        )

        hits = [{"call_id": int(h.id), "score": float(h.score)} for h in res[0]]
        return {"query": query, "count": len(hits), "results": hits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/search")
def search(query: str, top_k: int = 5, customer_id: str | None = None):
    """
    embed query → Milvus search → enrich with Postgres metadata
    Optional post-filter on `customer_id`.
    """
    try:
        # 1) Embed
        qvec = get_embedding(query)

        # 2) Milvus search
        col = Collection(COLLECTION_NAME)
        col.load()
        res = col.search(
            data=[qvec],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=[],
        )

        hits = res[0]
        ids = [int(h.id) for h in hits]
        if not ids:
            return {"query": query, "count": 0, "results": []}

        # 3) Fetch metadata from PG
        meta = _fetch_metadata(ids)  # returns {call_id: {...}}

        # 4) Optional post-filter
        results = []
        for h in hits:
            cid = int(h.id)
            m = meta.get(cid, {})
            if customer_id and (m.get("customer_id") != customer_id):
                continue
            results.append({
                "call_id": cid,
                "score": float(h.score),
                "external_id": m.get("external_id"),
                "customer_id": m.get("customer_id"),
                "started_at": m.get("started_at"),
                "duration_sec": m.get("duration_sec"),
                "file_uri": m.get("file_uri"),
                "summary": m.get("summary"),
                "sentiment": m.get("sentiment"),
            })

        return {"query": query, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))