import aiohttp
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    BASE_URL = "https://api.openai.com/v1/chat/completions"

    @property
    def name(self) -> str:
        return "OpenAI"

    async def generate(self, prompt: str, **kwargs) -> str:
        self.require_api_key("OpenAI")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": kwargs.get("model", "gpt-4o"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.3)
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, json=payload, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"OpenAI API error {resp.status}: {await resp.text()}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head("https://api.openai.com", timeout=5) as resp:
                    return resp.status < 500
        except Exception:
            return False

    def cost_estimate(self, prompt: str, output_tokens: int = 500) -> str:
        input_tokens = len(prompt) // 4
        cost = (input_tokens / 1e6) * 10.0 + (output_tokens / 1e6) * 30.0
        return f"~${cost:.4f} (GPT-4o, {input_tokens}+{output_tokens} tokens)"
