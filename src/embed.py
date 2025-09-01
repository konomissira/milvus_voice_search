# from sentence_transformers import SentenceTransformer
# from typing import List

# # "all-MiniLM-L6-v2" → 384-dimensional vectors
# _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# def get_embedding(text: str) -> List[float]:
#     """
#     Generate a 384-dim embedding for a single text string.
#     Returns a Python list of floats.
#     """
#     if not text or not text.strip():
#         raise ValueError("Input text is empty.")
#     embedding = _model.encode(text, convert_to_numpy=True).tolist()
#     return embedding

# if __name__ == "__main__":
#     # Quick sanity check
#     sample = "Milvus is an open-source vector database."
#     vec = get_embedding(sample)
#     print(f"Embedding length: {len(vec)}")
#     print(f"First 5 dims: {vec[:5]}")

from typing import List, Sequence
import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = SentenceTransformer(_MODEL_NAME)

def _normalize(arr: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return (arr / norms).astype(np.float32)

def get_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        raise ValueError("Input text is empty.")
    v = _model.encode([text], convert_to_numpy=True)
    v = _normalize(v)[0]
    return v.tolist()

def embed_texts(texts: Sequence[str]) -> List[List[float]]:
    if not texts:
        return []
    vs = _model.encode(list(texts), convert_to_numpy=True)
    vs = _normalize(vs)
    return [row.tolist() for row in vs]
