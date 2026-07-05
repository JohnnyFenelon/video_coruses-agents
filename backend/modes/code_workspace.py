import json
from pathlib import Path

from backend.orchestrator import orchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
}
MAX_FILE_BYTES = 250_000


class CodeWorkspace:
    def __init__(self, root: Path = PROJECT_ROOT):
        self.root = root.resolve()

    def safe_path(self, path: str) -> Path:
        candidate = (self.root / path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("Path is outside the project workspace")
        return candidate

    def relative_path(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()

    def tree(self, limit: int = 300) -> list[dict]:
        items = []
        for path in sorted(self.root.rglob("*")):
            rel = self.relative_path(path)
            if any(part in IGNORED_DIRS for part in path.relative_to(self.root).parts):
                continue
            items.append({
                "path": rel,
                "type": "directory" if path.is_dir() else "file",
                "size": path.stat().st_size if path.is_file() else 0,
            })
            if len(items) >= limit:
                break
        return items

    def read_file(self, path: str) -> dict:
        full_path = self.safe_path(path)
        if not full_path.exists() or not full_path.is_file():
            raise FileNotFoundError(path)
        if full_path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("File is too large to read in the app")
        return {
            "path": self.relative_path(full_path),
            "content": full_path.read_text(encoding="utf-8"),
        }

    def write_file(self, path: str, content: str) -> dict:
        full_path = self.safe_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return {
            "path": self.relative_path(full_path),
            "size": full_path.stat().st_size,
        }

    async def generate_code(self, prompt: str, provider: str = "", apply: bool = False) -> dict:
        workspace_summary = "\n".join(
            f"- {item['path']}" for item in self.tree(limit=180) if item["type"] == "file"
        )
        code_prompt = f"""You are editing the Johnny Agents project.

Workspace files:
{workspace_summary}

User request:
{prompt}

Return only valid JSON with this shape:
{{
  "summary": "short explanation",
  "files": [
    {{
      "path": "relative/path.ext",
      "action": "create_or_replace",
      "content": "complete new file content"
    }}
  ],
  "notes": ["short note"]
}}

Rules:
- Include complete file contents for every changed file.
- Keep paths relative to the project root.
- Do not wrap the JSON in markdown.
"""
        response = await orchestrator.chat(code_prompt, provider=provider)
        raw = response["result"]
        plan = self._parse_json(raw)
        applied = []
        if apply:
            for file_change in plan.get("files", []):
                if file_change.get("action") not in {"create_or_replace", "update"}:
                    continue
                content = file_change.get("content")
                path = file_change.get("path")
                if isinstance(path, str) and isinstance(content, str):
                    applied.append(self.write_file(path, content))
        return {
            "provider": response["provider"],
            "cost": response["cost"],
            "plan": plan,
            "raw": raw,
            "applied": applied,
        }

    def _parse_json(self, text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start:end + 1]
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "summary": "The model did not return valid JSON.",
                "files": [],
                "notes": ["Use the raw response to copy changes manually."],
                "raw": text,
            }
