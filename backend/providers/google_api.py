import aiohttp

from .base import BaseProvider


class GoogleProvider(BaseProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"

    @property
    def name(self) -> str:
        return "Google Gemini"

    async def generate(self, prompt: str, **kwargs) -> str:
        self.require_api_key("Google Gemini")
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        generation_config = {
            "temperature": kwargs.get("temperature", 0.3),
        }
        if kwargs.get("max_tokens"):
            generation_config["max_output_tokens"] = kwargs["max_tokens"]

        payload = {
            "model": kwargs.get("model", "gemini-3.5-flash"),
            "input": prompt,
            "generation_config": generation_config,
        }
        if kwargs.get("system_instruction"):
            payload["system_instruction"] = kwargs["system_instruction"]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.BASE_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Google Gemini API error {resp.status}: {await resp.text()}")
                data = await resp.json()
                return self._extract_text(data)

    async def is_available(self) -> bool:
        return bool(self.api_key)

    def cost_estimate(self, prompt: str, output_tokens: int = 500) -> str:
        input_tokens = len(prompt) // 4
        return f"Check Google AI Studio billing ({input_tokens}+{output_tokens} estimated tokens)"

    def _extract_text(self, data: dict) -> str:
        if isinstance(data.get("output_text"), str):
            return data["output_text"]

        chunks = []
        for step in data.get("steps", []):
            for item in step.get("content", []):
                text = item.get("text")
                if text:
                    chunks.append(text)
        if chunks:
            return "\n".join(chunks)

        candidates = data.get("candidates", [])
        for candidate in candidates:
            parts = candidate.get("content", {}).get("parts", [])
            for part in parts:
                text = part.get("text")
                if text:
                    chunks.append(text)
        if chunks:
            return "\n".join(chunks)

        return str(data)
