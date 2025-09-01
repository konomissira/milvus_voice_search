import os
from pymilvus import connections, Collection
from embed import get_embedding

MILVUS_HOST = os.getenv("MILVUS_HOST", "127.0.0.1")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION = "call_embeddings"

def search(query: str, topk: int = 3):
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
    col = Collection(COLLECTION)
    col.load()
    qvec = get_embedding(query)
    res = col.search(
        data=[qvec],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 10}},
        limit=topk,
        output_fields=[],
    )
    print(f"Query: {query}")
    for i, hit in enumerate(res[0], 1):
        print(f"{i}. id={hit.id}, score={hit.score:.4f}")

if __name__ == "__main__":
    search("refund for leaking coffee machine", topk=3)
