from sentence_transformers import SentenceTransformer

_shared_model = None


def get_shared_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Singleton provider for the SentenceTransformer embedding model.
    Loads on-demand to ensure instantaneous server startup and low RAM.
    """
    global _shared_model
    if _shared_model is None:
        print(f"Loading embedding model '{model_name}' on first use...", flush=True)
        _shared_model = SentenceTransformer(model_name)
        print("Embedding model loaded successfully.", flush=True)
    return _shared_model


class LazyEmbeddingModel:
    """
    Lightweight wrapper that defers SentenceTransformer loading until
    the first inference call (.encode()), preventing startup delays and port scan timeouts.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name

    def encode(self, *args, **kwargs):
        return get_shared_embedding_model(self.model_name).encode(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(get_shared_embedding_model(self.model_name), name)
