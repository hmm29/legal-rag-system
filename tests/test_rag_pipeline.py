from src.rag.pipeline import SYSTEM_PROMPT, RagPipeline, build_prompt
from src.vector_store.pinecone_store import Passage
from tests.fakes import FakeEmbedder, FakeLLM, FakeStore


def test_prompt_numbers_passages_and_names_sources():
    passages = [
        Passage(text="First passage.", source="a.txt", score=0.9),
        Passage(text="Second passage.", source="b.txt", score=0.8),
    ]
    prompt = build_prompt("What is an offer?", passages)
    assert "[1] (a.txt)\nFirst passage." in prompt
    assert "[2] (b.txt)\nSecond passage." in prompt
    assert prompt.rstrip().endswith("Question: What is an offer?\nAnswer:")


def test_answer_returns_text_and_its_sources():
    embedder, store, llm = FakeEmbedder(), FakeStore(), FakeLLM()
    pipeline = RagPipeline(embedder, store, llm, top_k=2)

    answer = pipeline.answer("What makes a contract valid?")

    assert answer.answer == llm.reply
    assert [passage.source for passage in answer.sources] == ["contract.txt", "contract.txt"]
    assert embedder.calls == [["What makes a contract valid?"]]
    assert store.searches[0][1] == 2
    system, prompt = llm.prompts[0]
    assert system == SYSTEM_PROMPT
    assert "An offer, acceptance and consideration." in prompt


def test_top_k_limits_the_passages_sent_to_the_model():
    store = FakeStore()
    llm = FakeLLM()
    RagPipeline(FakeEmbedder(), store, llm, top_k=1).answer("q")
    assert "[1]" in llm.prompts[0][1]
    assert "[2]" not in llm.prompts[0][1]


def test_no_passages_means_no_model_call():
    llm = FakeLLM()
    pipeline = RagPipeline(FakeEmbedder(), FakeStore(passages=[]), llm)
    answer = pipeline.answer("Something off-topic")
    assert answer.sources == []
    assert answer.answer.startswith("I don't know")
    assert llm.prompts == []
