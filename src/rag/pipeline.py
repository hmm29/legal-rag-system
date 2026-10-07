"""The retrieval-augmented generation step: retrieve passages, then answer from them."""
from dataclasses import dataclass

from src.vector_store.pinecone_store import Passage

SYSTEM_PROMPT = (
    "You are a legal research assistant. Answer the question using only the "
    "numbered passages provided. Cite the passages you rely on by number, like [1]. "
    "If the passages do not contain the answer, say you don't know. Do not guess."
)


@dataclass(frozen=True)
class Answer:
    answer: str
    sources: list[Passage]


def build_prompt(question: str, passages: list[Passage]) -> str:
    context = "\n\n".join(
        f"[{i}] ({passage.source})\n{passage.text}" for i, passage in enumerate(passages, start=1)
    )
    return f"Passages:\n\n{context}\n\nQuestion: {question}\nAnswer:"


class OpenAIChat:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.model = model
        self._api_key = api_key
        self._client = None

    def complete(self, system: str, prompt: str) -> str:
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()


class RagPipeline:
    """Embed the question, fetch the closest passages, and answer from them.

    Every answer comes back with the passages it was given, so a reader can
    check the answer against its sources.
    """

    def __init__(self, embedder, store, llm, top_k: int = 5):
        self.embedder = embedder
        self.store = store
        self.llm = llm
        self.top_k = top_k

    def answer(self, question: str) -> Answer:
        vector = self.embedder.embed([question])[0]
        passages = self.store.search(vector, top_k=self.top_k)
        if not passages:
            return Answer(
                answer="I don't know. No relevant passages were found for this question.",
                sources=[],
            )
        text = self.llm.complete(SYSTEM_PROMPT, build_prompt(question, passages))
        return Answer(answer=text, sources=passages)
