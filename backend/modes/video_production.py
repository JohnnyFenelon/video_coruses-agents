import json
from pathlib import Path
from datetime import datetime

from backend.orchestrator import orchestrator
from backend.config import settings


class VideoProductionPipeline:
    """Mode 2: Cinematic & Animated Video Production Flow"""

    SUB_STYLES = ["cinematic_realism", "3d_animation", "2d_anime", "singing_avatar"]

    def __init__(self):
        self.video_dir = Path(settings.preferences.get("output_dir", "data")) / "videos"

    async def run(self, blueprint: dict) -> dict:
        story = blueprint.get("story", "")
        style = blueprint.get("style", "cinematic_realism")
        if style not in self.SUB_STYLES:
            raise ValueError(f"Unknown style: {style}. Must be one of {self.SUB_STYLES}")

        manual_inputs = blueprint.get("agent_inputs", {}) or {}
        provided_characters = blueprint.get("characters", []) or []
        self.video_dir.mkdir(parents=True, exist_ok=True)
        project_name = story[:40].lower().replace(" ", "_").replace("\n", "_")
        project_dir = self.video_dir / project_name
        project_dir.mkdir(exist_ok=True)

        # Phase 0: Agent planning and context
        orchestrator_plan = await self._orchestrator_plan(story, style, manual_inputs.get("goal"))
        context_summary = await self._gather_context(story, style, manual_inputs.get("brand_voice"))
        research_notes = await self._research_insights(story, style, manual_inputs.get("research_focus"))
        (project_dir / "orchestrator.json").write_text(json.dumps(orchestrator_plan, indent=2), encoding="utf-8")
        (project_dir / "context_summary.json").write_text(json.dumps(context_summary, indent=2), encoding="utf-8")
        (project_dir / "research_notes.json").write_text(json.dumps(research_notes, indent=2), encoding="utf-8")
        (project_dir / "provided_characters.json").write_text(json.dumps(provided_characters, indent=2), encoding="utf-8")

        # Phase 1: Story & Scripting Agent
        script = await self._write_script(story, style, research_notes, context_summary, provided_characters)
        (project_dir / "script.json").write_text(json.dumps(script, indent=2), encoding="utf-8")

        # Phase 2: Character & Consistency Agent (Stable Diffusion prompts)
        character_sheets = await self._generate_character_sheets(script, style)
        (project_dir / "character_sheets.json").write_text(
            json.dumps(character_sheets, indent=2), encoding="utf-8"
        )

        # Phase 3: Style Guide
        style_guide = self._build_style_guide(style, script)
        (project_dir / "style_guide.md").write_text(style_guide, encoding="utf-8")

        # Phase 4: Shot Programming Agent
        shots = await self._program_shots(script, style_guide)
        (project_dir / "shots.json").write_text(json.dumps(shots, indent=2), encoding="utf-8")

        # Phase 5: Generate prompts for video engine
        video_prompts = []
        for shot in shots:
            # Append style guide for consistency
            full_prompt = f"{shot['prompt']}\n\nStyle: {style_guide}"
            shot["video_prompt"] = full_prompt
            video_prompts.append(shot)

        (project_dir / "video_prompts.json").write_text(
            json.dumps(video_prompts, indent=2), encoding="utf-8"
        )

        manifest = self._build_manifest(blueprint, script, shots)
        (project_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        critic_review = await self._critic_review(script, style, manual_inputs.get("review_notes"))
        fact_check = await self._fact_check(script, style)
        (project_dir / "critic_review.json").write_text(json.dumps(critic_review, indent=2), encoding="utf-8")
        (project_dir / "fact_check.json").write_text(json.dumps(fact_check, indent=2), encoding="utf-8")

        # Phase 6: Unified export bundle (JSON)
        export_bundle = {
            "manifest": manifest,
            "script": script,
            "character_sheets": character_sheets,
            "style_guide": style_guide,
            "shots": shots,
            "video_prompts": video_prompts,
            "orchestrator_plan": orchestrator_plan,
            "context_summary": context_summary,
            "research_notes": research_notes,
            "critic_review": critic_review,
            "fact_check": fact_check,
            "generated_at": datetime.now().isoformat()
        }
        (project_dir / "export.json").write_text(json.dumps(export_bundle, indent=2), encoding="utf-8")

        return {
            "status": "ready",
            "project_path": str(project_dir),
            "story": script.get("title", story[:50]),
            "scenes_count": len(script.get("scenes", [])),
            "shots_count": len(shots),
            "style": style,
            "files": [
                "orchestrator.json", "context_summary.json", "research_notes.json", "script.json",
                "character_sheets.json", "style_guide.md", "shots.json",
                "video_prompts.json", "critic_review.json", "fact_check.json", "manifest.json", "export.json"
            ],
            "sample_shots": shots[:5],
            "agent_outputs": {
                "orchestrator": orchestrator_plan,
                "context": context_summary,
                "research": research_notes,
                "critic": critic_review,
                "fact_check": fact_check
            },
            "characters": script.get("characters", []),
            "character_sheets": character_sheets,
            "provided_characters": provided_characters,
            "export_file": str(project_dir / "export.json"),
            "export_url": f"/api/video/download?path={project_dir.name}/export.json",
            "next_step": "Execute video_prompts.json through Pruna P-Video (use /api/video/generate_batch)"
        }

    async def _write_script(self, story: str, style: str, research_notes: dict | None = None, context_summary: dict | None = None) -> dict:
        prompt = f"""Write a cinematic video script based on this story concept:

Story: {story}
Style: {style}
Research notes: {research_notes or 'None'}
Context summary: {context_summary or 'None'}

Return a JSON object with:
- title: string
- logline: string
- style: "{style}"
- characters: [{{"name": "...", "description": "...", "personality": "..."}}]
- scenes: [{{"scene_number": 1, "location": "...", "time_of_day": "...", "summary": "...", "dialogue": "...", "emotional_beat": "...", "duration_seconds": 5}}]
- duration_estimate_seconds: number
"""
        result = await orchestrator.chat(prompt)
        text = result["result"]
        cleaned = text.strip().removeprefix("```json").removesuffix("```").strip() if "```" in text else text
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"title": "Untitled", "scenes": [], "raw": text}

    async def _generate_character_sheets(self, script: dict, style: str) -> list:
        characters = script.get("characters", [{"name": "protagonist", "description": "main character"}])
        sheets = []
        for char in characters:
            prompt = f"""Generate a character design sheet for a {style} video.

Character: {char.get('name')}
Description: {char.get('description')}
Personality: {char.get('personality', 'neutral')}

Return a JSON object with:
- character_name: string
- style: "{style}"
- front_view_prompt: (Stable Diffusion prompt for front view)
- side_view_prompt: (Stable Diffusion prompt for side view)
- back_view_prompt: (Stable Diffusion prompt for back view)
- expression_prompts: {{"happy": "...", "sad": "...", "angry": "...", "neutral": "..."}}
- consistency_keywords: [list of visual keywords for consistency]
"""
            result = await orchestrator.chat(prompt)
            text = result["result"]
            cleaned = text.strip().removeprefix("```json").removesuffix("```").strip() if "```" in text else text
            try:
                sheets.append(json.loads(cleaned))
            except json.JSONDecodeError:
                sheets.append({"character_name": char.get('name'), "raw": text})
        return sheets

    async def _format_character_definitions(self, characters: list[dict]) -> str:
        if not characters:
            return "Auto-generate characters based on story and style."
        lines = []
        for idx, char in enumerate(characters, start=1):
            name = char.get("name", "Unnamed")
            desc = char.get("description", "No description provided")
            personality = char.get("personality", "Neutral")
            lines.append(f"Character {idx}: Name: {name}; Description: {desc}; Personality: {personality}")
        return "\n".join(lines)

    async def _orchestrator_plan(self, story: str, style: str, goal: str | None) -> dict:
        prompt = f"""You are the Orchestrator agent. Create a clear production plan for a short cinematic video.
Story concept: {story}
Style: {style}
Goal: {goal or 'Create a compelling short video story.'}

Return JSON with:
- objective: string
- timeline: string
- key_outputs: [list of strings]
- notes: string
"""
        result = await orchestrator.chat(prompt)
        return self._parse_json_result(result["result"], default={"objective": "Plan generated", "timeline": "1-2 days", "key_outputs": [], "notes": ""})

    async def _gather_context(self, story: str, style: str, brand_voice: str | None) -> dict:
        prompt = f"""You are the Context agent. Summarize the project context for the video.
Story concept: {story}
Style: {style}
Brand voice: {brand_voice or 'modern and emotional'}

Return JSON with:
- brand_voice: string
- tone: string
- target_audience: string
- visual_direction: string
"""
        result = await orchestrator.chat(prompt)
        return self._parse_json_result(result["result"], default={"brand_voice": brand_voice or "modern and emotional", "tone": "inspiring", "target_audience": "general viewers", "visual_direction": "cinematic"})

    async def _research_insights(self, story: str, style: str, research_focus: str | None) -> dict:
        prompt = f"""You are the Researcher agent. Gather insight notes for the video.
Story concept: {story}
Style: {style}
Research focus: {research_focus or 'character motivation and emotional arc'}

Return JSON with:
- research_summary: string
- inspirational_references: [list of strings]
- creative_direction: string
"""
        result = await orchestrator.chat(prompt)
        return self._parse_json_result(result["result"], default={"research_summary": "Key motivation and emotional arc.", "inspirational_references": [], "creative_direction": "emotional and cinematic"})

    async def _critic_review(self, script: dict, style: str, review_notes: str | None) -> dict:
        prompt = f"""You are the Critic agent. Review the script for clarity, pacing, and emotional impact.
Script title: {script.get('title')}
Style: {style}
Review notes: {review_notes or 'None'}

Return JSON with:
- critique: string
- improvements: [list of strings]
- confidence: string
"""
        result = await orchestrator.chat(prompt)
        return self._parse_json_result(result["result"], default={"critique": "Script looks good.", "improvements": [], "confidence": "high"})

    async def _fact_check(self, script: dict, style: str) -> dict:
        prompt = f"""You are the Fact-Checker agent. Verify consistency, logic, and any factual references in the script.
Script title: {script.get('title')}
Style: {style}

Return JSON with:
- status: string
- issues_found: [list of strings]
- notes: string
"""
        result = await orchestrator.chat(prompt)
        return self._parse_json_result(result["result"], default={"status": "checked", "issues_found": [], "notes": "No major issues detected."})

    def _parse_json_result(self, text: str, default: dict) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {**default, "raw": text}

    def _build_style_guide(self, style: str, script: dict) -> str:
        guides = {
            "cinematic_realism": (
                "Cinematic Realism: Photorealistic, 35mm film look, shallow depth of field, "
                "natural lighting, film grain, 24fps, anamorphic lens flares, "
                "color graded with teal-orange palette, ultra-detailed textures, ray-traced global illumination."
            ),
            "3d_animation": (
                "3D Animation (Pixar-style): Stylized 3D render, exaggerated proportions, "
                "smooth subsurface scattering, warm lighting, vibrant saturated colors, "
                "bouncy rigging, 30fps, blur-free renders, toy-like textures with stylized shaders."
            ),
            "2d_anime": (
                "2D Anime: Hand-drawn aesthetic, cel-shaded, bold line art, "
                "soft pastel palette, dramatic eye reflections, "
                "sakura bloom color grading, 24fps, 2D rigging with keyframe interpolation, "
                "screen-tones and halftone patterns for shadows."
            ),
            "singing_avatar": (
                "Singing Avatar: VTuber-style, semi-realistic anime, "
                "focused on lip-sync accuracy, expressive eyes, "
                "stage lighting with spotlights, 30fps, "
                "clean background (green screen ready), upper-body framing."
            )
        }
        base = guides.get(style, guides["cinematic_realism"])
        characters = script.get("characters", [])
        char_desc = "\n".join([
            f"- {c.get('name')}: {c.get('description')}" for c in characters
        ])
        return f"""# Style Guide - {style}

{base}

## Characters
{char_desc or "- Generic protagonist"}

## Visual Consistency Rules
- Maintain exact same character proportions across all shots
- Use consistent color palette (refer to character sheet)
- Keep lighting direction consistent within scenes
- Apply same post-processing grade across entire video
"""
        return base

    async def _program_shots(self, script: dict, style_guide: str) -> list:
        scenes = script.get("scenes", [])
        all_shots = []
        shot_id = 0

        for scene in scenes:
            duration = scene.get("duration_seconds", 5)
            # ~1 shot per second
            for second in range(duration):
                shot_id += 1
                prompt = f"""Generate a video generation prompt for shot {shot_id} (second {second+1} of {duration}):

Scene {scene.get('scene_number')}: {scene.get('summary')}
Location: {scene.get('location')}
Time: {scene.get('time_of_day')}
Emotional beat: {scene.get('emotional_beat', 'neutral')}

Camera: {"wide shot establishing the scene" if second == 0 else "close-up on character reaction" if second == duration-1 else "medium shot following action"}
Lighting: {"soft warm lighting" if scene.get('time_of_day') == 'day' else "dramatic low-key lighting" if scene.get('time_of_day') == 'night' else "natural lighting"}

Return JSON:
{{
  "shot_id": {shot_id},
  "scene": {scene.get('scene_number')},
  "second": {second+1},
  "camera_angle": "...",
  "lighting": "...",
  "action_description": "...",
  "prompt": "(detailed Stable Diffusion / Pruna video prompt)"
}}
"""
                result = await orchestrator.chat(prompt)
                text = result["result"]
                cleaned = text.strip().removeprefix("```json").removesuffix("```").strip() if "```" in text else text
                try:
                    shot_data = json.loads(cleaned)
                except json.JSONDecodeError:
                    shot_data = {
                        "shot_id": shot_id,
                        "scene": scene.get("scene_number"),
                        "second": second + 1,
                        "camera_angle": "medium",
                        "lighting": "natural",
                        "action_description": scene.get("summary", ""),
                        "prompt": text
                    }
                all_shots.append(shot_data)

        return all_shots

    def _build_manifest(self, blueprint: dict, script: dict, shots: list) -> dict:
        return {
            "title": script.get("title", blueprint.get("story", "Untitled")[:60]),
            "style": blueprint.get("style", "cinematic_realism"),
            "logline": script.get("logline", ""),
            "duration_seconds": sum(s.get("duration_seconds", 5) for s in script.get("scenes", [])),
            "shots_count": len(shots),
            "scenes": script.get("scenes", []),
            "characters": script.get("characters", []),
            "generated_at": datetime.now().isoformat(),
            "format_version": "2.0",
            "status": "prompts_ready"
        }
