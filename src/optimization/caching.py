"""On-disk cache of answers, keyed by the normalized question."""
import hashlib
import json
from pathlib import Path


class ResultCache:
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(question: str) -> str:
        normalized = " ".join(question.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _path(self, question: str) -> Path:
        return self.cache_dir / f"{self.key(question)}.json"

    def get(self, question: str) -> dict | None:
        path = self._path(question)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, question: str, result: dict) -> None:
        self._path(question).write_text(json.dumps(result), encoding="utf-8")

    def clear(self) -> int:
        removed = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink()
            removed += 1
        return removed
