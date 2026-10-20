from sentence_transformers import SentenceTransformer

_shared_model = None


def get_shared_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Singleton provider for the SentenceTransformer embedding model.
    Prevents loading multiple duplicate copies in memory, reducing
    RAM consumption from ~1.2GB down to ~350MB.
    """
    global _shared_model
    if _shared_model is None:
        _shared_model = SentenceTransformer(model_name)
    return _shared_model
