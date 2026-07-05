import json
from datetime import datetime
from pathlib import Path


HISTORY_PATH = Path(__file__).resolve().parents[1] / "data" / "chat_history.json"
MAX_HISTORY_ITEMS = 300


class ChatHistory:
    def __init__(self, path: Path = HISTORY_PATH):
        self.path = path

    def list(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        return data

    def add(self, prompt: str, response: str, provider: str, cost: str = "") -> dict:
        item = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "created_at": datetime.now().isoformat(),
            "provider": provider,
            "cost": cost,
            "prompt": prompt,
            "response": response,
        }
        items = [item] + self.list()
        items = items[:MAX_HISTORY_ITEMS]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")
        return item

    def clear(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("[]", encoding="utf-8")


chat_history = ChatHistory()
