"""Stand-ins for the embedding model, vector store and chat model."""
from src.vector_store.pinecone_store import Passage


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.append(list(texts))
        return [[float(len(text)), 1.0, 0.0] for text in texts]


class FakeStore:
    def __init__(self, passages=None):
        self.passages = (
            passages
            if passages is not None
            else [
                Passage(text="An offer, acceptance and consideration.", source="contract.txt", score=0.9),
                Passage(text="Mutual assent is also required.", source="contract.txt", score=0.8),
            ]
        )
        self.searches = []

    def search(self, vector, top_k=5):
        self.searches.append((vector, top_k))
        return self.passages[:top_k]


class FakeLLM:
    def __init__(self, reply="A contract needs offer, acceptance and consideration [1]."):
        self.reply = reply
        self.prompts = []

    def complete(self, system, prompt):
        self.prompts.append((system, prompt))
        return self.reply


def raises(exception_type, fn, *args, **kwargs):
    """True if calling fn raises exception_type."""
    try:
        fn(*args, **kwargs)
    except exception_type:
        return True
    return False
