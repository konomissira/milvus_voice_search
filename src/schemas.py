from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection, utility
)

COLLECTION_NAME = "call_embeddings"
DIM = 384  # embedding size from sentence-transformers

def connect_milvus(host: str = "localhost", port: str = "19530"):
    # Connect to Milvus server.
    connections.connect(alias="default", host=host, port=port)
    print("Connected to Milvus")

def ensure_collection():
    # Ensure a Milvus collection for call embeddings exists.
    if utility.has_collection(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' already exists.")
        return Collection(COLLECTION_NAME)

    # Define schema
    fields = [
        FieldSchema(
            name="call_id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=False,
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=DIM,
        ),
    ]
    schema = CollectionSchema(fields, description="Call transcript embeddings")
    collection = Collection(name=COLLECTION_NAME, schema=schema)

    # Create index
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    print(f"Created collection '{COLLECTION_NAME}' with index.")
    return collection

def insert_embeddings(call_ids, vectors):
    """
    Insert a batch of embeddings into Milvus.
    call_ids: list[int]
    vectors: list[list[float]]
    """
    collection = Collection(COLLECTION_NAME)
    data = [call_ids, vectors]
    mr = collection.insert(data)
    collection.flush()
    print(f"Inserted {len(call_ids)} embeddings into '{COLLECTION_NAME}'.")
    return mr

if __name__ == "__main__":
    connect_milvus()
    ensure_collection()
