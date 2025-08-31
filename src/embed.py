from sentence_transformers import SentenceTransformer
from typing import List

# "all-MiniLM-L6-v2" → 384-dimensional vectors
_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def get_embedding(text: str) -> List[float]:
    """
    Generate a 384-dim embedding for a single text string.
    Returns a Python list of floats.
    """
    if not text or not text.strip():
        raise ValueError("Input text is empty.")
    embedding = _model.encode(text, convert_to_numpy=True).tolist()
    return embedding

if __name__ == "__main__":
    # Quick sanity check
    sample = "Milvus is an open-source vector database."
    vec = get_embedding(sample)
    print(f"Embedding length: {len(vec)}")
    print(f"First 5 dims: {vec[:5]}")
