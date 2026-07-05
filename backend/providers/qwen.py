import aiohttp
from .base import BaseProvider


class QwenProvider(BaseProvider):
    BASE_URL = "https://api.wavespeed.ai/v1/chat/completions"

    @property
    def name(self) -> str:
        return "Qwen 2.5 7B"

    async def generate(self, prompt: str, **kwargs) -> str:
        self.require_api_key("Qwen")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": kwargs.get("model", "qwen2.5-7b"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.3)
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, json=payload, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Qwen API error {resp.status}: {await resp.text()}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(self.BASE_URL, timeout=5) as resp:
                    return resp.status < 500
        except Exception:
            return False

    def cost_estimate(self, prompt: str, output_tokens: int = 500) -> str:
        input_tokens = len(prompt) // 4
        cost = (input_tokens / 1e6) * 0.15 + (output_tokens / 1e6) * 0.60
        return f"~${cost:.5f} (Qwen 2.5 7B, {input_tokens}+{output_tokens} tokens)"
