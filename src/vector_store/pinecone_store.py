"""Embeddings and the Pinecone index that stores them."""
import time
from dataclasses import dataclass

from src.data.data_preparation import Chunk


@dataclass(frozen=True)
class Passage:
    text: str
    source: str
    score: float


class SentenceTransformerEmbedder:
    """Local embedding model. Loaded on first use, since it is a large import."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


class PineconeStore:
    """Thin wrapper over one Pinecone index.

    Pass `client` to inject a fake in tests. Otherwise a real client is built
    from `api_key`.
    """

    def __init__(
        self,
        index_name: str,
        dimension: int,
        api_key: str | None = None,
        cloud: str = "aws",
        region: str = "us-east-1",
        client=None,
    ):
        self.index_name = index_name
        self.dimension = dimension
        self._cloud = cloud
        self._region = region
        if client is None:
            from pinecone import Pinecone

            client = Pinecone(api_key=api_key)
        self._client = client
        self._index = None

    def ensure_index(self, timeout_seconds: float = 120.0) -> None:
        """Create the index if it does not exist and wait until it is ready."""
        if self.index_name not in self._client.list_indexes().names():
            from pinecone import ServerlessSpec

            self._client.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=self._cloud, region=self._region),
            )
        deadline = time.monotonic() + timeout_seconds
        while not self._client.describe_index(self.index_name).status["ready"]:
            if time.monotonic() > deadline:
                raise TimeoutError(f"Pinecone index {self.index_name} was not ready in time")
            time.sleep(1)

    @property
    def index(self):
        if self._index is None:
            self._index = self._client.Index(self.index_name)
        return self._index

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]], batch_size: int = 100) -> int:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must be the same length")
        for start in range(0, len(chunks), batch_size):
            batch = [
                {
                    "id": chunk.id,
                    "values": vector,
                    "metadata": {"text": chunk.text, "source": chunk.source},
                }
                for chunk, vector in zip(
                    chunks[start : start + batch_size], vectors[start : start + batch_size]
                )
            ]
            self.index.upsert(vectors=batch)
        return len(chunks)

    def search(self, vector: list[float], top_k: int = 5) -> list[Passage]:
        response = self.index.query(vector=vector, top_k=top_k, include_metadata=True)
        passages = []
        for match in response.matches:
            metadata = match.metadata or {}
            passages.append(
                Passage(
                    text=metadata.get("text", ""),
                    source=metadata.get("source", ""),
                    score=float(match.score),
                )
            )
        return passages

    def count(self) -> int:
        return int(self.index.describe_index_stats().total_vector_count)
