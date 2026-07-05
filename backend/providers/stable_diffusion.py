import aiohttp
import base64
from .base import BaseProvider


class StableDiffusionProvider(BaseProvider):
    BASE_URL = "https://api.runpod.ai/v2/stable-diffusion-xl/runsync"

    @property
    def name(self) -> str:
        return "Stable Diffusion"

    async def generate(self, prompt: str, **kwargs) -> str:
        self.require_api_key("Stable Diffusion")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": {
                "prompt": prompt,
                "negative_prompt": kwargs.get("negative_prompt", ""),
                "width": kwargs.get("width", 1024),
                "height": kwargs.get("height", 1024),
                "num_inference_steps": kwargs.get("steps", 30),
                "guidance_scale": kwargs.get("cfg_scale", 7.5),
                "scheduler": kwargs.get("scheduler", "DPMSolverMultistepScheduler"),
                "num_images": kwargs.get("num_images", 1)
            }
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, json=payload, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"SD API error {resp.status}: {await resp.text()}")
                data = await resp.json()
                output = data.get("output")
                if isinstance(output, list) and len(output) > 0:
                    return output[0]
                return str(data)

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
        return "~$0.01–0.05 per image (Stable Diffusion XL)"
