import aiohttp
from .base import BaseProvider


class ClaudeProvider(BaseProvider):
    BASE_URL = "https://api.anthropic.com/v1/messages"

    @property
    def name(self) -> str:
        return "Claude"

    async def generate(self, prompt: str, **kwargs) -> str:
        self.require_api_key("Claude")
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": kwargs.get("model", "claude-sonnet-4-20250514"),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": [{"role": "user", "content": prompt}]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, json=payload, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Claude API error {resp.status}: {await resp.text()}")
                data = await resp.json()
                return data["content"][0]["text"]

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head("https://api.anthropic.com", timeout=5) as resp:
                    return resp.status < 500
        except Exception:
            return False

    def cost_estimate(self, prompt: str, output_tokens: int = 500) -> str:
        input_tokens = len(prompt) // 4
        cost = (input_tokens / 1e6) * 3.0 + (output_tokens / 1e6) * 15.0
        return f"~${cost:.4f} (Claude Sonnet 4, {input_tokens}+{output_tokens} tokens)"
