from backend.config import settings
from backend.providers import PROVIDER_REGISTRY, BaseProvider


class AIOrchestrator:
    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}
        self.llm_provider_order = ["google", "custom_qwen", "openai", "claude", "glm", "qwen"]

    def get_provider(self, name: str) -> BaseProvider:
        if name not in self._providers:
            cls = PROVIDER_REGISTRY.get(name)
            if not cls:
                raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDER_REGISTRY.keys())}")
            api_key = settings.get_api_key(name)
            self._providers[name] = cls(api_key=api_key)
        return self._providers[name]

    def refresh_provider(self, name: str | None = None):
        if name:
            self._providers.pop(name, None)
            return
        self._providers.clear()

    def resolve_llm(self, preferred: str = "") -> BaseProvider:
        preferred = preferred or settings.preferences.get("default_llm", "qwen")
        if not settings.get_api_key(preferred):
            configured = self.first_configured_llm()
            if not configured:
                raise RuntimeError("No LLM API key is configured. Add a Google, OpenAI, Claude, GLM, or Qwen key in Settings.")
            preferred = configured
        primary = self.get_provider(preferred)
        fallback_name = self.first_configured_llm(exclude=preferred)
        if fallback_name:
            fallback = self.get_provider(fallback_name)
            return primary.with_fallback(fallback)
        return primary

    def first_configured_llm(self, exclude: str = "") -> str:
        for provider in self.llm_provider_order:
            if provider != exclude and settings.get_api_key(provider):
                return provider
        return ""

    def resolve_video(self) -> BaseProvider:
        engine = settings.preferences.get("default_video_engine", "pruna")
        return self.get_provider(engine)

    def resolve_image(self) -> BaseProvider:
        return self.get_provider("stable_diffusion")

    async def chat(self, prompt: str, provider: str = "", **kwargs) -> dict:
        llm = self.resolve_llm(provider)
        cost = llm.cost_estimate(prompt)
        result = await llm.generate(prompt, **kwargs)
        return {"provider": llm.name, "cost": cost, "result": result}

    async def generate_video(self, prompt: str, **kwargs) -> dict:
        engine = self.resolve_video()
        cost = engine.cost_estimate(prompt)
        result = await engine.generate(prompt, **kwargs)
        return {"provider": engine.name, "cost": cost, "result": result}

    async def generate_image(self, prompt: str, **kwargs) -> dict:
        engine = self.resolve_image()
        cost = engine.cost_estimate(prompt)
        result = await engine.generate(prompt, **kwargs)
        return {"provider": engine.name, "cost": cost, "result": result}

    def available_providers(self) -> list[dict]:
        providers = []
        for key, cls in PROVIDER_REGISTRY.items():
            api_key = settings.get_api_key(key)
            providers.append({
                "id": key,
                "name": cls(api_key=api_key).name,
                "configured": bool(api_key),
            })
        return providers


orchestrator = AIOrchestrator()
