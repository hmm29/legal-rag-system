"""Settings, read once from environment variables."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    pinecone_api_key: str
    openai_api_key: str
    index_name: str = "legal-documents"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    chat_model: str = "gpt-4o-mini"
    top_k: int = 5
    max_qps: int = 20
    batch_workers: int = 5
    cache_dir: str = "./cache"


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is not set. Export it or add it to a .env file before starting."
        )
    return value


def load_settings() -> Settings:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    env = os.environ
    return Settings(
        pinecone_api_key=_required("PINECONE_API_KEY"),
        openai_api_key=_required("OPENAI_API_KEY"),
        index_name=env.get("PINECONE_INDEX", "legal-documents"),
        pinecone_cloud=env.get("PINECONE_CLOUD", "aws"),
        pinecone_region=env.get("PINECONE_REGION", "us-east-1"),
        chat_model=env.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        top_k=int(env.get("RAG_TOP_K", "5")),
        max_qps=int(env.get("RAG_MAX_QPS", "20")),
        batch_workers=int(env.get("RAG_BATCH_WORKERS", "5")),
        cache_dir=env.get("RAG_CACHE_DIR", "./cache"),
    )
