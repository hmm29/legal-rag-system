"""Load documents, embed them and index them in Pinecone.

Usage: python -m scripts.ingest --docs sample_docs
"""
import argparse

from src.config import load_settings
from src.data.data_preparation import chunk_documents, load_documents
from src.vector_store.pinecone_store import PineconeStore, SentenceTransformerEmbedder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", default="sample_docs", help="directory of .txt files")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=200)
    args = parser.parse_args()

    settings = load_settings()
    documents = load_documents(args.docs)
    chunks = chunk_documents(documents, args.chunk_size, args.overlap)
    print(f"Loaded {len(documents)} documents, split into {len(chunks)} chunks")

    embedder = SentenceTransformerEmbedder(settings.embedding_model)
    vectors = embedder.embed([chunk.text for chunk in chunks])

    store = PineconeStore(
        index_name=settings.index_name,
        dimension=settings.embedding_dim,
        api_key=settings.pinecone_api_key,
        cloud=settings.pinecone_cloud,
        region=settings.pinecone_region,
    )
    store.ensure_index()
    store.upsert(chunks, vectors)
    print(f"Indexed {len(chunks)} chunks in Pinecone index '{settings.index_name}'")


if __name__ == "__main__":
    main()
