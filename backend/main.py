from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional

from backend.config import settings
from backend.chat_history import chat_history
from backend.orchestrator import orchestrator
from backend.modes import CourseCreationPipeline, VideoProductionPipeline
from backend.modes.code_workspace import CodeWorkspace
from backend.providers import PROVIDER_REGISTRY

import uvicorn

app = FastAPI(title="Johnny Agents", version="3.0.0")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class ChatRequest(BaseModel):
    prompt: str
    provider: str = ""

class CodeGenerateRequest(BaseModel):
    prompt: str
    provider: str = ""
    apply: bool = False

class WorkspaceWriteRequest(BaseModel):
    path: str
    content: str

class GenerateVideoRequest(BaseModel):
    prompt: str
    mode: str = "text-to-video"
    width: int = 1024
    height: int = 576
    num_frames: int = 25
    fps: int = 24

class GenerateVideoBatchRequest(BaseModel):
    prompts: list[dict]
    width: int = 1024
    height: int = 576
    num_frames: int = 25
    fps: int = 24

class GenerateImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024

class CourseBlueprint(BaseModel):
    title: str = ""
    topic: str = ""
    audience: str = "beginners"
    difficulty: str = "beginner"
    modules: list[dict] = []
    generate_assets: bool = True
    references: list[str] = []
    auto_generate_blueprint: bool = True

class VideoBlueprint(BaseModel):
    story: str
    style: str = "cinematic_realism"
    agent_inputs: dict = Field(default_factory=dict)
    characters: list[dict] = Field(default_factory=list)

class SetApiKeyRequest(BaseModel):
    provider: str
    key: str

class SetProviderConfigRequest(BaseModel):
    provider: str
    config: dict

class CronJobRequest(BaseModel):
    schedule: str
    command: str
    mode: str = "course"
    label: str = ""

# --- API Routes ---

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

@app.get("/api/providers")
async def list_providers():
    return {"providers": orchestrator.available_providers()}

@app.get("/api/config")
async def get_config():
    preferred_llm = settings.preferences.get("default_llm", "qwen")
    effective_llm = preferred_llm
    if not settings.get_api_key(preferred_llm):
        effective_llm = orchestrator.first_configured_llm()
    return {
        "api_keys": {k: "***" if v else "" for k, v in settings.api_keys.items()},
        "provider_configs": masked_provider_configs(),
        "preferences": settings.preferences,
        "effective_llm": effective_llm,
        "cron_jobs": settings.cron_jobs
    }

def masked_provider_configs() -> dict:
    configs = {}
    for provider, config in settings.provider_configs.items():
        safe = dict(config)
        if safe.get("password"):
            safe["password"] = "***"
        configs[provider] = safe
    return configs

@app.post("/api/config/api-key")
async def set_api_key(req: SetApiKeyRequest):
    if req.provider not in PROVIDER_REGISTRY:
        raise HTTPException(400, f"Unknown provider: {req.provider}")
    settings.set_api_key(req.provider, req.key)
    orchestrator.refresh_provider(req.provider)
    return {"status": "ok", "provider": req.provider}

@app.delete("/api/config/api-key/{provider}")
async def remove_api_key(provider: str):
    if provider not in PROVIDER_REGISTRY:
        raise HTTPException(400, f"Unknown provider: {provider}")
    settings.remove_api_key(provider)
    orchestrator.refresh_provider(provider)
    return {"status": "ok", "provider": provider}

@app.post("/api/config/provider")
async def set_provider_config(req: SetProviderConfigRequest):
    if req.provider not in PROVIDER_REGISTRY:
        raise HTTPException(400, f"Unknown provider: {req.provider}")
    config = dict(req.config)
    if config.get("password") == "***":
        config.pop("password")
    settings.set_provider_config(req.provider, config)
    orchestrator.refresh_provider(req.provider)
    return {"status": "ok", "provider": req.provider}

@app.delete("/api/config/provider/{provider}")
async def remove_provider_config(provider: str):
    if provider not in PROVIDER_REGISTRY:
        raise HTTPException(400, f"Unknown provider: {provider}")
    settings.remove_provider_config(provider)
    orchestrator.refresh_provider(provider)
    return {"status": "ok", "provider": provider}

@app.post("/api/config/preferences")
async def set_preferences(prefs: dict):
    settings._data["preferences"].update(prefs)
    settings.save()
    return {"status": "ok"}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        result = await orchestrator.chat(req.prompt, provider=req.provider)
        item = chat_history.add(
            prompt=req.prompt,
            response=result["result"],
            provider=result["provider"],
            cost=result["cost"],
        )
        result["chat_id"] = item["id"]
        return result
    except Exception as e:
        chat_history.add(
            prompt=req.prompt,
            response=f"Error: {e}",
            provider=req.provider or "auto",
            cost="failed",
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history")
async def list_chat_history():
    return {"items": chat_history.list()}

@app.delete("/api/chat/history")
async def clear_chat_history():
    chat_history.clear()
    return {"status": "ok"}

@app.get("/api/workspace/tree")
async def workspace_tree():
    try:
        return {"root": str(CodeWorkspace().root), "items": CodeWorkspace().tree()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workspace/file")
async def workspace_read_file(path: str):
    try:
        return CodeWorkspace().read_file(path)
    except FileNotFoundError:
        raise HTTPException(404, f"File not found: {path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/workspace/file")
async def workspace_write_file(req: WorkspaceWriteRequest):
    try:
        return CodeWorkspace().write_file(req.path, req.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/code/generate")
async def code_generate(req: CodeGenerateRequest):
    try:
        return await CodeWorkspace().generate_code(req.prompt, provider=req.provider, apply=req.apply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/video/generate")
async def generate_video(req: GenerateVideoRequest):
    try:
        result = await orchestrator.generate_video(
            req.prompt,
            mode=req.mode,
            width=req.width,
            height=req.height,
            num_frames=req.num_frames,
            fps=req.fps
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/video/generate_batch")
async def generate_video_batch(req: GenerateVideoBatchRequest):
    try:
        results = []
        for item in req.prompts:
            prompt = item.get("video_prompt") or item.get("prompt")
            if not prompt:
                continue
            result = await orchestrator.generate_video(
                prompt,
                mode="text-to-video",
                width=req.width,
                height=req.height,
                num_frames=req.num_frames,
                fps=req.fps
            )
            results.append({
                "shot_id": item.get("shot_id"),
                "provider": result["provider"],
                "cost": result["cost"],
                "result": result["result"],
            })
        return {"status": "complete", "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/image/generate")
async def generate_image(req: GenerateImageRequest):
    try:
        result = await orchestrator.generate_image(
            req.prompt,
            width=req.width,
            height=req.height
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/course/blueprint")
async def generate_course_blueprint(blueprint: CourseBlueprint):
    try:
        pipeline = CourseCreationPipeline()
        generated = await pipeline.generate_blueprint(blueprint.model_dump())
        return {"status": "ok", "blueprint": generated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/course/create")
async def create_course(blueprint: CourseBlueprint):
    try:
        pipeline = CourseCreationPipeline()
        result = await pipeline.run(blueprint.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/video/create")
async def create_video(blueprint: VideoBlueprint):
    try:
        pipeline = VideoProductionPipeline()
        result = await pipeline.run(blueprint.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cron/add")
async def add_cron(req: CronJobRequest):
    job = {
        "id": f"job_{len(settings.cron_jobs) + 1}",
        "schedule": req.schedule,
        "command": req.command,
        "mode": req.mode,
        "label": req.label,
        "enabled": True
    }
    settings.add_cron_job(job)
    return {"status": "ok", "job": job}

@app.get("/api/cron/list")
async def list_crons():
    return {"jobs": settings.cron_jobs}

@app.delete("/api/cron/{job_id}")
async def remove_cron(job_id: str):
    settings.remove_cron_job(job_id)
    return {"status": "ok"}

@app.get("/api/course/download")
async def download_course(path: str):
    try:
        archive = Path(settings.preferences.get("output_dir", "data")) / "courses" / path
        if not archive.exists():
            raise HTTPException(404, "Course archive not found")
        return FileResponse(str(archive), media_type="application/zip", filename=archive.name)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/logs")
async def get_logs():
    log_dir = Path(settings.preferences.get("output_dir", "data")) / "logs"
    if not log_dir.exists():
        return {"logs": []}
    logs = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    entries = []
    for log in logs[:20]:
        entries.append({
            "name": log.name,
            "size": log.stat().st_size,
            "modified": log.stat().st_mtime
        })
    return {"logs": entries}


@app.get("/api/video/download")
async def download_video(path: str):
    try:
        archive = Path(settings.preferences.get("output_dir", "data")) / "videos" / path
        if not archive.exists():
            raise HTTPException(404, "Video export not found")
        return FileResponse(str(archive), media_type="application/json", filename=archive.name)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/file")
async def read_file(path: str):
    try:
        full = CodeWorkspace().safe_path(path)
    except Exception as e:
        raise HTTPException(400, str(e))
    if not full.exists() or not full.is_file():
        raise HTTPException(404, f"File not found: {path}")
    if full.suffix == ".json":
        return full.read_text(encoding="utf-8")
    return {"content": full.read_text(encoding="utf-8")[:10000]}

# --- Frontend Static Routes (must be last, after all API routes) ---
if FRONTEND_DIR.exists():
    @app.get("/")
    async def serve_index():
        return HTMLResponse((FRONTEND_DIR / "index.html").read_text(encoding="utf-8"))

    @app.get("/css/{file_path:path}")
    async def serve_css(file_path: str):
        fp = FRONTEND_DIR / "css" / file_path
        if fp.exists() and fp.is_file():
            return FileResponse(str(fp))
        raise HTTPException(404)

    @app.get("/js/{file_path:path}")
    async def serve_js(file_path: str):
        fp = FRONTEND_DIR / "js" / file_path
        if fp.exists() and fp.is_file():
            return FileResponse(str(fp))
        raise HTTPException(404)

    @app.get("/courses/{course_name}/site")
    @app.get("/courses/{course_name}/site/{path:path}")
    async def serve_course_site(course_name: str, path: str = ""):
        course_root = Path(settings.preferences.get("output_dir", "data")) / "courses" / course_name / "site"
        if not course_root.exists() or not course_root.is_dir():
            raise HTTPException(404, "Course site not found")

        candidate = course_root / path if path else course_root / "index.html"
        if not candidate.exists() or not candidate.is_file():
            fallback = course_root / "index.html"
            if fallback.exists() and fallback.is_file():
                return FileResponse(str(fallback))
            raise HTTPException(404, "Course page not found")
        return FileResponse(str(candidate))

    @app.api_route("/{path:path}", methods=["GET"])
    async def spa_fallback(path: str):
        fp = FRONTEND_DIR / path
        if fp.exists() and fp.is_file():
            return FileResponse(str(fp))
        return HTMLResponse((FRONTEND_DIR / "index.html").read_text(encoding="utf-8"))


def start():
    uvicorn.run("backend.main:app", host="0.0.0.0", port=3000, reload=True)


if __name__ == "__main__":
    start()
