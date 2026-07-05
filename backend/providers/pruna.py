import aiohttp
from .base import BaseProvider


class PrunaProvider(BaseProvider):
    BASE_URL = "https://api.runpod.ai/v2/pruna-pvideo/runsync"

    @property
    def name(self) -> str:
        return "Pruna P-Video"

    async def generate(self, prompt: str, **kwargs) -> str:
        self.require_api_key("Pruna")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        mode = kwargs.get("mode", "text-to-video")
        payload = {
            "input": {
                "prompt": prompt,
                "mode": mode,
                "negative_prompt": kwargs.get("negative_prompt", ""),
                "width": kwargs.get("width", 1024),
                "height": kwargs.get("height", 576),
                "num_frames": kwargs.get("num_frames", 25),
                "fps": kwargs.get("fps", 24),
                "cfg_scale": kwargs.get("cfg_scale", 7.0),
                "steps": kwargs.get("steps", 25)
            }
        }
        if mode == "image-to-video" and kwargs.get("input_image"):
            payload["input"]["input_image"] = kwargs["input_image"]
        if mode == "audio-to-video" and kwargs.get("input_audio"):
            payload["input"]["input_audio"] = kwargs["input_audio"]

        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, json=payload, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=300)) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Pruna API error {resp.status}: {await resp.text()}")
                data = await resp.json()
                return data.get("output", {}).get("video_url", str(data))

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head("https://api.runpod.ai", timeout=5) as resp:
                    return resp.status < 500
        except Exception:
            return False

    def cost_estimate(self, prompt: str, output_tokens: int = 500) -> str:
        return "~$0.10–0.50 per video (Pruna P-Video, depends on resolution & frames)"
