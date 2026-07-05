from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    def cost_estimate(self, prompt: str, output_tokens: int = 500) -> str:
        return "Cost estimate unavailable"

    def require_api_key(self, label: str | None = None):
        if not self.api_key:
            raise RuntimeError(f"{label or self.name} API key is not configured")

    def with_fallback(self, fallback_provider: "BaseProvider"):
        return ProviderWithFallback(self, fallback_provider)


class ProviderWithFallback(BaseProvider):
    def __init__(self, primary: BaseProvider, fallback: BaseProvider):
        self.primary = primary
        self.fallback = fallback

    @property
    def name(self) -> str:
        return f"{self.primary.name}+{self.fallback.name}"

    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            return await self.primary.generate(prompt, **kwargs)
        except Exception as e:
            print(f"[Fallback] {self.primary.name} failed: {e}. Trying {self.fallback.name}...")
            return await self.fallback.generate(prompt, **kwargs)

    async def is_available(self) -> bool:
        return await self.primary.is_available() or await self.fallback.is_available()

    def cost_estimate(self, prompt: str, output_tokens: int = 500) -> str:
        return f"Fallback chain: {self.primary.cost_estimate(prompt, output_tokens)} | {self.fallback.cost_estimate(prompt, output_tokens)}"
