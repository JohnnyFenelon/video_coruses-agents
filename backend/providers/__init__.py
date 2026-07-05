from .base import BaseProvider
from .glm import GLMProvider
from .qwen import QwenProvider
from .openai_api import OpenAIProvider
from .claude_api import ClaudeProvider
from .google_api import GoogleProvider
from .custom_qwen import CustomQwenProvider
from .pruna import PrunaProvider
from .stable_diffusion import StableDiffusionProvider
from .google_video import GoogleVideoProvider

PROVIDER_REGISTRY = {
    "google": GoogleProvider,
    "google_video": GoogleVideoProvider,
    "custom_qwen": CustomQwenProvider,
    "glm": GLMProvider,
    "qwen": QwenProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "pruna": PrunaProvider,
    "stable_diffusion": StableDiffusionProvider,
}

__all__ = ["BaseProvider", "PROVIDER_REGISTRY"]
