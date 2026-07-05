import asyncio
import time
from pathlib import Path

from .base import BaseProvider


def _load_genai_client(api_key: str):
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "The google-genai package is not installed. "
            "Install it in your virtual environment with: .\\.venv\\Scripts\\pip install google-genai"
        ) from exc
    return genai.Client(api_key=api_key)


class GoogleVideoProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "Google GenAI Video"

    async def generate(self, prompt: str, **kwargs) -> dict:
        return await asyncio.to_thread(self._generate_video, prompt, **kwargs)

    def _generate_video(self, prompt: str, **kwargs) -> dict:
        self.require_api_key("Google GenAI")
        output_dir = kwargs.get("output_dir")
        output_name = kwargs.get("output_name", "generated_video.mp4")
        model = kwargs.get("model", "veo-3.1-generate-preview")
        poll_interval = kwargs.get("poll_interval", 10)

        if not output_dir:
            raise RuntimeError("Google video generation requires an output_dir")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        client = _load_genai_client(self.api_key)

        operation = client.models.generate_videos(model=model, prompt=prompt)
        while not operation.done:
            time.sleep(poll_interval)
            operation = client.operations.get(operation)

        generated_video = operation.response.generated_videos[0]
        download = client.files.download(file=generated_video.video)

        video_file = output_path / output_name
        if hasattr(download, "save"):
            download.save(str(video_file))
        else:
            data = download if isinstance(download, (bytes, bytearray)) else download.read()
            video_file.write_bytes(data)

        return {"video_path": str(video_file)}

    async def is_available(self) -> bool:
        try:
            _load_genai_client(self.api_key)
            return bool(self.api_key)
        except RuntimeError:
            return False

    def cost_estimate(self, prompt: str, output_tokens: int = 500) -> str:
        return "Google GenAI video estimate depends on your Google account and model usage"
