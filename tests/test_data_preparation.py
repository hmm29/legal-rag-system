import tempfile
from pathlib import Path

from src.data.data_preparation import chunk_documents, load_documents, split_text
from tests.fakes import raises


def test_short_text_is_one_chunk():
    assert split_text("A short clause.") == ["A short clause."]


def test_empty_text_gives_no_chunks():
    assert split_text("   \n  ") == []


def test_chunks_respect_size_limit():
    text = "This is a sentence about contracts. " * 100
    chunks = split_text(text, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(chunk) <= 200 for chunk in chunks)


def test_chunks_overlap_so_nothing_is_lost():
    words = [f"word{i}" for i in range(400)]
    text = " ".join(words)
    chunks = split_text(text, chunk_size=300, overlap=60)
    joined = " ".join(chunks)
    assert all(word in joined for word in words)


def test_prefers_sentence_boundaries():
    text = ("Alpha beta gamma delta. " * 20).strip()
    chunks = split_text(text, chunk_size=110, overlap=10)
    assert all(chunk.endswith(".") for chunk in chunks)


def test_invalid_settings_are_rejected():
    assert raises(ValueError, split_text, "text", 0, 0)
    assert raises(ValueError, split_text, "text", 100, 100)
    assert raises(ValueError, split_text, "text", 100, -1)


def test_load_and_chunk_documents():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("First document. " * 30, encoding="utf-8")
        (root / "nested").mkdir()
        (root / "nested" / "b.txt").write_text("Second document.", encoding="utf-8")
        (root / "empty.txt").write_text("  ", encoding="utf-8")
        (root / "ignored.md").write_text("Not a text file.", encoding="utf-8")

        documents = load_documents(tmp)
        assert [doc.source for doc in documents] == ["a.txt", str(Path("nested") / "b.txt")]

        chunks = chunk_documents(documents, chunk_size=120, overlap=20)
        assert chunks[0].id == "a.txt#0"
        assert len({chunk.id for chunk in chunks}) == len(chunks)
        assert chunks[-1].source == str(Path("nested") / "b.txt")


def test_missing_directory_raises():
    assert raises(FileNotFoundError, load_documents, "/no/such/directory")
