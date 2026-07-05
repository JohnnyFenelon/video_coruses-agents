import aiohttp
from urllib.parse import urlsplit, urlunsplit, unquote

from backend.config import settings
from .base import BaseProvider


class CustomQwenProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "Custom Qwen Server"

    async def generate(self, prompt: str, **kwargs) -> str:
        config = settings.get_provider_config("custom_qwen")
        endpoint_url = config.get("endpoint_url", "").strip()
        if not endpoint_url:
            raise RuntimeError("Custom Qwen endpoint URL is not configured")

        endpoint_url, auth = self._build_auth(endpoint_url, config)
        parts = urlsplit(endpoint_url)
        if not parts.path or parts.path in ("/", ""):
            endpoint_url = endpoint_url.rstrip("/") + "/api/chat"

        payload = {
            "model": kwargs.get("model") or config.get("model") or "qwen2.5:7b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(
                endpoint_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                body = await resp.text()
                if resp.status != 200:
                    raise RuntimeError(f"Custom Qwen API error {resp.status}: {body}")
                try:
                    data = await resp.json()
                except Exception:
                    return body
                return self._extract_text(data)

    async def is_available(self) -> bool:
        return bool(settings.get_provider_config("custom_qwen").get("endpoint_url"))

    def cost_estimate(self, prompt: str, output_tokens: int = 500) -> str:
        return "Local/custom endpoint cost depends on your server"

    def _build_auth(self, endpoint_url: str, config: dict):
        parts = urlsplit(endpoint_url)
        username = config.get("username") or unquote(parts.username or "")
        password = config.get("password") or unquote(parts.password or "")
        auth = aiohttp.BasicAuth(username, password) if username or password else None

        if parts.username or parts.password:
            host = parts.hostname or ""
            if parts.port:
                host = f"{host}:{parts.port}"
            endpoint_url = urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))

        return endpoint_url, auth

    def _extract_text(self, data):
        if isinstance(data, str):
            return data
        message = data.get("message") if isinstance(data, dict) else None
        if isinstance(message, dict) and message.get("content"):
            return message["content"]
        if isinstance(data, dict) and data.get("response"):
            return data["response"]
        if isinstance(data, dict) and data.get("output"):
            return data["output"]
        choices = data.get("choices", []) if isinstance(data, dict) else []
        if choices:
            content = choices[0].get("message", {}).get("content")
            if content:
                return content
        return str(data)
