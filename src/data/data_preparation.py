"""Load plain-text legal documents and split them into overlapping chunks."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    text: str
    source: str


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source: str


def load_documents(directory: str) -> list[Document]:
    """Read every .txt file under `directory`, recursively."""
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(f"Document directory not found: {directory}")
    documents = []
    for path in sorted(root.rglob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            documents.append(Document(text=text, source=str(path.relative_to(root))))
    return documents


def split_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into chunks of at most `chunk_size` characters.

    Consecutive chunks share up to `overlap` characters so a sentence that
    straddles a boundary is still retrievable. Where possible a chunk ends at
    a paragraph or sentence break instead of mid-sentence.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be at least 0 and smaller than chunk_size")
    text = text.strip()
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            sentence_end = window.rfind(". ")
            cut = max(
                window.rfind("\n\n"),
                sentence_end + 1 if sentence_end != -1 else -1,
            )
            if cut > chunk_size // 2:
                end = start + cut
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_documents(
    documents: list[Document], chunk_size: int = 1000, overlap: int = 200
) -> list[Chunk]:
    chunks = []
    for doc in documents:
        for i, piece in enumerate(split_text(doc.text, chunk_size, overlap)):
            chunks.append(Chunk(id=f"{doc.source}#{i}", text=piece, source=doc.source))
    return chunks
