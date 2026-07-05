import json
import os
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


class Settings:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        return {
            "api_keys": {
                "openai": "",
                "google": "",
                "custom_qwen": "",
                "glm": "",
                "qwen": "",
                "claude": "",
                "pruna": "",
                "stable_diffusion": "",
                "google_video": ""
            },
            "provider_configs": {
                "custom_qwen": {
                    "endpoint_url": "",
                    "username": "",
                    "password": "",
                    "model": "qwen2.5-coder"
                }
            },
            "preferences": {
                "default_llm": "qwen",
                "default_video_engine": "pruna",
                "output_dir": str(Path(__file__).parent.parent / "data"),
                "log_level": "INFO"
            },
            "cron_jobs": []
        }

    def save(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def api_keys(self) -> dict:
        return self._data.get("api_keys", {})

    def get_api_key(self, provider: str) -> str:
        if provider == "custom_qwen":
            return self.get_provider_config("custom_qwen").get("endpoint_url", "")
        key = self.api_keys.get(provider, "") or os.environ.get(f"{provider.upper()}_API_KEY", "")
        if provider == "qwen" and key.lower().startswith(("http://", "https://")):
            return ""
        return key

    def set_api_key(self, provider: str, key: str):
        self._data.setdefault("api_keys", {})[provider] = key
        self.save()

    def remove_api_key(self, provider: str):
        self._data.setdefault("api_keys", {})[provider] = ""
        self.save()

    @property
    def provider_configs(self) -> dict:
        return self._data.setdefault("provider_configs", {})

    def get_provider_config(self, provider: str) -> dict:
        return self.provider_configs.get(provider, {})

    def set_provider_config(self, provider: str, config: dict):
        existing = self.provider_configs.get(provider, {})
        existing.update(config)
        self.provider_configs[provider] = existing
        self.save()

    def remove_provider_config(self, provider: str):
        if provider == "custom_qwen":
            self.provider_configs[provider] = {
                "endpoint_url": "",
                "username": "",
                "password": "",
                "model": "qwen2.5-coder"
            }
        else:
            self.provider_configs.pop(provider, None)
        self.save()

    @property
    def preferences(self) -> dict:
        return self._data.get("preferences", {})

    @property
    def cron_jobs(self) -> list:
        return self._data.get("cron_jobs", [])

    def add_cron_job(self, job: dict):
        self._data.setdefault("cron_jobs", []).append(job)
        self.save()

    def remove_cron_job(self, job_id: str):
        self._data["cron_jobs"] = [j for j in self._data.get("cron_jobs", []) if j.get("id") != job_id]
        self.save()


settings = Settings()
