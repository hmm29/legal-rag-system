from types import SimpleNamespace

from src.data.data_preparation import Chunk
from src.vector_store.pinecone_store import PineconeStore
from tests.fakes import raises


class FakeIndex:
    def __init__(self):
        self.upserts = []
        self.queries = []

    def upsert(self, vectors):
        self.upserts.append(vectors)

    def query(self, vector, top_k, include_metadata):
        self.queries.append((vector, top_k, include_metadata))
        return SimpleNamespace(
            matches=[
                SimpleNamespace(id="a#0", score=0.91, metadata={"text": "Alpha", "source": "a.txt"}),
                SimpleNamespace(id="b#0", score=0.5, metadata=None),
            ]
        )

    def describe_index_stats(self):
        return SimpleNamespace(total_vector_count=7)


class FakeClient:
    def __init__(self, existing=("legal-documents",)):
        self.existing = list(existing)
        self.created = []
        self.index = FakeIndex()

    def list_indexes(self):
        return SimpleNamespace(names=lambda: list(self.existing))

    def create_index(self, **kwargs):
        self.created.append(kwargs)
        self.existing.append(kwargs["name"])

    def describe_index(self, name):
        return SimpleNamespace(status={"ready": True})

    def Index(self, name):
        return self.index


def make_store(client):
    return PineconeStore(index_name="legal-documents", dimension=3, client=client)


def test_upsert_sends_text_and_source_as_metadata_in_batches():
    client = FakeClient()
    store = make_store(client)
    chunks = [Chunk(id=f"a#{i}", text=f"text {i}", source="a.txt") for i in range(5)]
    vectors = [[float(i), 0.0, 1.0] for i in range(5)]

    assert store.upsert(chunks, vectors, batch_size=2) == 5

    assert [len(batch) for batch in client.index.upserts] == [2, 2, 1]
    first = client.index.upserts[0][0]
    assert first == {"id": "a#0", "values": [0.0, 0.0, 1.0], "metadata": {"text": "text 0", "source": "a.txt"}}


def test_upsert_rejects_mismatched_lengths():
    store = make_store(FakeClient())
    chunk = Chunk(id="a#0", text="t", source="a.txt")
    assert raises(ValueError, store.upsert, [chunk], [])


def test_search_maps_matches_to_passages():
    client = FakeClient()
    passages = make_store(client).search([0.1, 0.2, 0.3], top_k=2)

    assert client.index.queries == [([0.1, 0.2, 0.3], 2, True)]
    assert (passages[0].text, passages[0].source, passages[0].score) == ("Alpha", "a.txt", 0.91)
    assert (passages[1].text, passages[1].source) == ("", "")


def test_existing_index_is_not_recreated_and_count_reads_stats():
    client = FakeClient()
    store = make_store(client)
    store.ensure_index()
    assert client.created == []
    assert store.count() == 7
