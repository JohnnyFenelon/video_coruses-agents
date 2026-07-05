import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

from backend.orchestrator import orchestrator
from backend.config import settings


class CourseCreationPipeline:
    """Mode 1: Automated Course Creation Flow"""

    def __init__(self):
        self.course_dir = Path(settings.preferences.get("output_dir", "data")) / "courses"

    async def run(self, blueprint: dict) -> dict:
        title = blueprint.get("title", "Untitled Course")
        topic = blueprint.get("topic", "")
        audience = blueprint.get("audience", "beginners")
        modules = blueprint.get("modules", [])

        if not modules or blueprint.get("auto_generate_blueprint"):
            blueprint = await self.generate_blueprint(blueprint)
            modules = blueprint.get("modules", [])

        self.course_dir.mkdir(parents=True, exist_ok=True)
        course_root = self.course_dir / title.lower().replace(" ", "_")
        course_root.mkdir(exist_ok=True)

        # Phase 1: Blueprint Analysis
        analysis = await self._analyze_blueprint(blueprint)

        # Write analysis
        (course_root / "course_analysis.json").write_text(
            json.dumps(analysis, indent=2), encoding="utf-8"
        )

        # Phase 2: Module Content Generation
        modules_output = []
        for mod in modules:
            module_content = await self._generate_module(mod, topic, audience)
            mod_dir = course_root / mod.get("slug", f"module_{modules.index(mod)}")
            mod_dir.mkdir(exist_ok=True)
            (mod_dir / "lesson_plan.json").write_text(
                json.dumps(module_content["lesson_plan"], indent=2), encoding="utf-8"
            )
            (mod_dir / "script.md").write_text(module_content["script"], encoding="utf-8")
            if module_content.get("quiz"):
                (mod_dir / "quiz.json").write_text(
                    json.dumps(module_content["quiz"], indent=2), encoding="utf-8"
                )
            modules_output.append({
                "slug": mod.get("slug"),
                "title": mod.get("title"),
                "status": "generated",
                "files": ["lesson_plan.json", "script.md", "quiz.json"]
            })

        # Phase 3: Asset generation prompts (Stable Diffusion)
        assets = []
        if blueprint.get("generate_assets", True):
            for mod in modules:
                asset_prompts = await self._generate_asset_prompts(mod, topic)
                assets.append(asset_prompts)

        # Phase 4: Manifest
        manifest = self._build_manifest(blueprint, analysis, modules_output)
        (course_root / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

        # Phase 5: Build deployable rich course experience
        site_dir = course_root / "site"
        self._build_react_site(course_root, site_dir, manifest, modules_output)
        archive_path = self._create_zip_bundle(course_root, site_dir)

        return {
            "status": "complete",
            "course_path": str(course_root),
            "modules_count": len(modules_output),
            "modules": modules_output,
            "assets_prompts": assets,
            "manifest": manifest,
            "analysis": analysis,
            "blueprint": blueprint,
            "site_dir": str(site_dir),
            "site_url": f"/courses/{course_root.name}/site/",
            "download_url": f"/api/course/download?path={course_root.name}.zip"
        }

    async def generate_blueprint(self, blueprint: dict) -> dict:
        title = (blueprint.get("title") or blueprint.get("topic") or "Untitled Course").strip()
        topic = (blueprint.get("topic") or "").strip()
        audience = blueprint.get("audience", "beginners")
        difficulty = blueprint.get("difficulty", "beginner")
        references = blueprint.get("references") or []
        if isinstance(references, str):
            references = [r.strip() for r in references.splitlines() if r.strip()]

        reference_text = "\n".join(references) if references else "None"
        prompt = f"""Create a compact course blueprint for a course titled \"{title}\" covering the topic \"{topic}\".
Audience: {audience}
Difficulty: {difficulty}
Reference links/resources:
{reference_text}

Return ONLY valid JSON with this structure:
{{
  "title": "{title}",
  "topic": "{topic}",
  "audience": "{audience}",
  "difficulty": "{difficulty}",
  "description": "short description",
  "learning_objectives": ["..."],
  "prerequisites": ["..."],
  "estimated_duration_hours": 4,
  "references": ["https://example.com"],
  "modules": [
    {{"title": "Intro", "description": "...", "slug": "intro", "objectives": ["..."], "duration_minutes": 45, "resources": ["https://example.com"]}}
  ]
}}
"""
        try:
            result = await orchestrator.chat(prompt)
            text = result["result"]
            cleaned = text.strip().removeprefix("```json").removesuffix("```").strip() if "```" in text else text
            data = json.loads(cleaned)
        except Exception:
            data = self._build_default_blueprint(title, topic, audience, difficulty, references)

        if not data.get("modules"):
            data["modules"] = self._build_default_modules(topic or title, references)

        data.setdefault("title", title)
        data.setdefault("topic", topic)
        data.setdefault("audience", audience)
        data.setdefault("difficulty", difficulty)
        data.setdefault("references", references)
        data.setdefault("generate_assets", blueprint.get("generate_assets", True))
        data.setdefault("auto_generate_blueprint", False)
        return data

    def _build_default_blueprint(self, title: str, topic: str, audience: str, difficulty: str, references: list) -> dict:
        return {
            "title": title or topic or "Untitled Course",
            "topic": topic,
            "audience": audience,
            "difficulty": difficulty,
            "description": f"A structured course covering {topic or title}",
            "learning_objectives": [
                f"Understand the fundamentals of {topic or title}",
                f"Apply practical examples for {topic or title}",
                f"Build confidence through guided exercises"
            ],
            "prerequisites": ["Basic familiarity with the subject"],
            "estimated_duration_hours": 4,
            "references": references or ["https://example.com/reference"],
            "modules": self._build_default_modules(topic or title, references)
        }

    def _build_default_modules(self, topic: str, references: list) -> list:
        base_topic = topic or "the subject"
        return [
            {
                "title": f"Introduction to {base_topic}",
                "description": f"Foundational concepts and overview of {base_topic}",
                "slug": "intro",
                "objectives": [f"Explain the core idea behind {base_topic}", f"Recognize common terminology"],
                "duration_minutes": 45,
                "resources": references[:3] or ["https://example.com/reference"]
            },
            {
                "title": f"Practical Applications of {base_topic}",
                "description": f"Hands-on examples and real-world scenarios for {base_topic}",
                "slug": "applications",
                "objectives": [f"Apply the concepts in simple exercises", f"Connect theory to practice"],
                "duration_minutes": 45,
                "resources": references[:3] or ["https://example.com/reference"]
            },
            {
                "title": f"Project-Based Learning for {base_topic}",
                "description": f"Build a small project using {base_topic}",
                "slug": "project",
                "objectives": [f"Create a mini project using {base_topic}", f"Review what was learned"],
                "duration_minutes": 45,
                "resources": references[:3] or ["https://example.com/reference"]
            }
        ]

    async def _analyze_blueprint(self, blueprint: dict) -> dict:
        prompt = f"""Analyze this course blueprint and extract structured metadata:

Title: {blueprint.get('title')}
Topic: {blueprint.get('topic')}
Audience: {blueprint.get('audience')}
Difficulty: {blueprint.get('difficulty', 'beginner')}
Modules: {[m.get('title') for m in blueprint.get('modules', [])]}

Return a JSON object with:
- learning_objectives (list of strings)
- target_audience_analysis (string)
- prerequisite_skills (list of strings)
- estimated_duration_hours (number)
- pedagogical_approach (string)
- module_sequence_analysis (string)
"""
        try:
            result = await orchestrator.chat(prompt)
            text = result["result"]
            cleaned = text.strip().removeprefix("```json").removesuffix("```").strip() if "```" in text else text
            return json.loads(cleaned)
        except Exception:
            topic = blueprint.get("topic") or blueprint.get("title") or "the course"
            return {
                "learning_objectives": [f"Understand the core concepts of {topic}"],
                "target_audience_analysis": f"Suitable for {blueprint.get('audience', 'learners')}",
                "prerequisite_skills": ["Basic familiarity with the subject"],
                "estimated_duration_hours": 4,
                "pedagogical_approach": "Structured, beginner-friendly explanation with practical examples",
                "module_sequence_analysis": "The content is organized into a clear introductory progression"
            }

    async def _generate_module(self, module: dict, topic: str, audience: str) -> dict:
        title = module.get("title", "Untitled Module")
        prompt = f"""Create a detailed educational module for a course on "{topic}" aimed at {audience}.

Module: {title}
Description: {module.get('description', '')}

Generate THREE outputs separated exactly by "---SECTION---":

1. LESSON PLAN (JSON):
{{
  "module_title": "...",
  "duration_minutes": 45,
  "sections": [{{"title": "...", "duration_minutes": 10, "key_points": ["..."]}}],
  "activities": ["..."],
  "resources": ["..."]
}}

2. SCRIPT (Markdown):
Full lecture script with talking points, examples, and transitions.

3. QUIZ (JSON):
{{
  "questions": [
    {{"question": "...", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "..."}}
  ]
}}

---SECTION---
"""
        try:
            result = await orchestrator.chat(prompt)
            text = result["result"]
            sections = text.split("---SECTION---")

            lesson_plan = {}
            script = text
            quiz = []

            if len(sections) >= 1:
                try:
                    lesson_plan = json.loads(sections[0].strip().removeprefix("```json").removesuffix("```").strip())
                except json.JSONDecodeError:
                    lesson_plan = {"raw": sections[0]}
            if len(sections) >= 2:
                script = sections[1].strip()
            if len(sections) >= 3:
                try:
                    quiz = json.loads(sections[2].strip().removeprefix("```json").removesuffix("```").strip())
                except json.JSONDecodeError:
                    quiz = {"raw": sections[2]}

            return {"lesson_plan": lesson_plan, "script": script, "quiz": quiz}
        except Exception:
            return {
                "lesson_plan": {
                    "module_title": title,
                    "duration_minutes": 45,
                    "sections": [
                        {"title": "Overview", "duration_minutes": 15, "key_points": [f"Overview of {topic}"]},
                        {"title": "Examples", "duration_minutes": 15, "key_points": ["Apply the concept"]},
                        {"title": "Exercise", "duration_minutes": 15, "key_points": ["Practice independently"]}
                    ],
                    "activities": ["Review the main concepts", "Complete a short guided exercise"],
                    "resources": ["https://example.com/reference"]
                },
                "script": f"# {title}\n\nThis lesson introduces {topic} with a simple overview and practical examples.",
                "quiz": {"questions": [{"question": f"What is the main focus of {title}?", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "This is a placeholder quiz generated because the AI service was unavailable."}]}
            }

    async def _generate_asset_prompts(self, module: dict, topic: str) -> list:
        prompt = f"""For the course topic "{topic}", module "{module.get('title')}",
generate 3 Stable Diffusion image prompts for educational diagrams/infographics.
Return as a JSON array of strings.
"""
        try:
            result = await orchestrator.chat(prompt)
            text = result["result"]
            cleaned = text.strip().removeprefix("```json").removesuffix("```").strip() if "```" in text else text
            return json.loads(cleaned)
        except Exception:
            return [f"Diagram prompt for {topic} module {module.get('title', 'intro')}"]

    def _build_manifest(self, blueprint: dict, analysis: dict, modules: list) -> dict:
        return {
            "title": blueprint.get("title"),
            "topic": blueprint.get("topic"),
            "audience": blueprint.get("audience"),
            "difficulty": blueprint.get("difficulty", "beginner"),
            "learning_objectives": analysis.get("learning_objectives", []),
            "prerequisites": analysis.get("prerequisite_skills", []),
            "estimated_duration_hours": analysis.get("estimated_duration_hours", 0),
            "pedagogical_approach": analysis.get("pedagogical_approach", ""),
            "modules": modules,
            "generated_at": datetime.now().isoformat(),
            "lms_ready": True,
            "format_version": "1.0"
        }

    def _build_react_site(self, course_root: Path, site_dir: Path, manifest: dict, modules: list):
        site_dir.mkdir(parents=True, exist_ok=True)
        (site_dir / "src").mkdir(exist_ok=True)
        (site_dir / "public").mkdir(exist_ok=True)

        package_json = {
            "name": f"course-{course_root.name}",
            "private": True,
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
                "lucide-react": "^0.468.0",
                "three": "^0.173.0",
                "@react-three/fiber": "^8.17.1",
                "@react-three/drei": "^9.15.0"
            },
            "devDependencies": {
                "@vitejs/plugin-react": "^4.3.1",
                "vite": "^5.4.10"
            }
        }
        (site_dir / "package.json").write_text(json.dumps(package_json, indent=2), encoding="utf-8")
        (site_dir / "vite.config.js").write_text(
            "import { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\n\nexport default defineConfig({ plugins: [react()] });\n",
            encoding="utf-8"
        )
        (site_dir / "index.html").write_text(
            "<!DOCTYPE html>\n<html lang=\"en\">\n  <head>\n    <meta charset=\"UTF-8\" />\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />\n    <title>Course Experience</title>\n  </head>\n  <body>\n    <div id=\"root\"></div>\n    <script type=\"module\" src=\"./src/main.jsx\"></script>\n  </body>\n</html>\n",
            encoding="utf-8"
        )
        (site_dir / "preview.html").write_text(
            "<!DOCTYPE html>\n<html lang=\"en\">\n  <head>\n    <meta charset=\"UTF-8\" />\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />\n    <title>Course Preview</title>\n    <style>body{margin:0;font-family:Inter,sans-serif;background:linear-gradient(135deg,#071325,#1d4ed8 55%,#7c3aed);color:#f8fafc}main{max-width:1000px;margin:0 auto;padding:24px} .card{background:rgba(255,255,255,.12);padding:20px;border-radius:24px;margin-bottom:16px}h1{margin-top:0}</style>\n  </head>\n  <body>\n    <main>\n      <section class=\"card\">\n        <h1>🎓 Course Preview</h1>\n        <p>Icons, emojis, and 3D-inspired visuals are ready for this course experience.</p>\n      </section>\n      <section class=\"card\">\n        <h2>✨ Highlights</h2>\n        <p>📚 Guided lessons • 🎮 Quizzes • 🧠 3D visuals • 🚀 Khan-style progression</p>\n      </section>\n    </main>\n  </body>\n</html>\n",
            encoding="utf-8"
        )

        manifest_json = json.dumps(manifest, indent=2)
        app_jsx_template = """import React from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Float } from '@react-three/drei';
import { BookOpen, Sparkles, PlayCircle, Trophy, Rocket, BrainCircuit } from 'lucide-react';
import './styles.css';

const manifest = __MANIFEST_JSON__;

function FloatingOrb() {
  const meshRef = React.useRef(null);
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.4;
      meshRef.current.rotation.y += delta * 0.5;
    }
  });

  return (
    <Float speed={2.2} rotationIntensity={1.2} floatIntensity={1.6}>
      <mesh ref={meshRef} position={[0, 0.3, 0]}>
        <torusKnotGeometry args={[0.7, 0.2, 180, 18]} />
        <meshStandardMaterial color="#7c3aed" emissive="#312e81" roughness={0.2} metalness={0.7} />
      </mesh>
    </Float>
  );
}

function App() {
  const moduleCount = manifest.modules?.length || 0;
  const totalMinutes = (manifest.modules || []).reduce((sum, module) => sum + (module.duration_minutes || 0), 0);

  return (
    <div className="course-shell">
      <header className="hero-card">
        <div className="hero-copy">
          <div className="badge-row">
            <span className="pill">✨ Interactive learning</span>
            <span className="pill">🎯 Khan-style mastery path</span>
          </div>
          <h1>{manifest.title || 'Course Experience'}</h1>
          <p>{manifest.topic || 'A polished learning journey with visuals, practice and progress.'}</p>
          <div className="hero-actions">
            <a className="primary-btn" href="#modules">Start learning</a>
            <span className="secondary-pill"><Sparkles size={16} /> Rich multimedia ready</span>
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <BookOpen size={18} />
              <div>
                <strong>{moduleCount}</strong>
                <span>Modules</span>
              </div>
            </div>
            <div className="stat-card">
              <Trophy size={18} />
              <div>
                <strong>{Math.ceil(totalMinutes / 60)}h</strong>
                <span>Estimated time</span>
              </div>
            </div>
          </div>
        </div>
        <div className="hero-visual">
          <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
            <ambientLight intensity={0.8} />
            <directionalLight position={[2, 3, 3]} intensity={1.2} />
            <FloatingOrb />
            <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={1.2} />
          </Canvas>
        </div>
      </header>

      <section className="content-grid">
        <article className="panel">
          <div className="panel-title">
            <BrainCircuit size={20} />
            <h2>What you will learn</h2>
          </div>
          <ul>
            {(manifest.learning_objectives || []).map((objective, index) => (
              <li key={index}>🎯 {objective}</li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <div className="panel-title">
            <Rocket size={20} />
            <h2>Course highlights</h2>
          </div>
          <div className="chip-stack">
            <span className="chip">📚 Guided lessons</span>
            <span className="chip">🎮 Interactive quizzes</span>
            <span className="chip">🧠 3D visual aids</span>
            <span className="chip">✨ Emoji-rich UI</span>
          </div>
        </article>
      </section>

      <section id="modules" className="modules-section">
        <div className="panel-title">
          <PlayCircle size={20} />
          <h2>Modules</h2>
        </div>
        <div className="module-list">
          {(manifest.modules || []).map((module, index) => (
            <div className="module-card" key={module.slug || index}>
              <div className="module-head">
                <span className="module-index">0{index + 1}</span>
                <span className="module-status">{module.status || 'ready'}</span>
              </div>
              <h3>{module.title}</h3>
              <p>{module.description || 'A structured lesson designed for mastery.'}</p>
              <div className="module-meta">
                <span>🕒 {module.duration_minutes || 45} min</span>
                <span>📁 {module.files?.join(', ') || 'lesson_plan.json, script.md'}</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
"""
        app_jsx = app_jsx_template.replace("__MANIFEST_JSON__", manifest_json)
        (site_dir / "src" / "App.jsx").write_text(app_jsx, encoding="utf-8")
        (site_dir / "src" / "main.jsx").write_text(
            "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nimport './styles.css';\n\nReactDOM.createRoot(document.getElementById('root')).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n);\n",
            encoding="utf-8"
        )
        (site_dir / "src" / "styles.css").write_text(
            "body { margin: 0; font-family: Inter, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #071325, #1d4ed8 55%, #7c3aed); color: #f8fafc; }\n* { box-sizing: border-box; }\na { text-decoration: none; }\n.course-shell { max-width: 1200px; margin: 0 auto; padding: 24px; }\n.hero-card { display: grid; grid-template-columns: 1.2fr 0.9fr; gap: 24px; padding: 28px; border-radius: 28px; background: rgba(7, 19, 37, 0.7); border: 1px solid rgba(255,255,255,0.16); box-shadow: 0 20px 60px rgba(0,0,0,0.25); backdrop-filter: blur(20px); }\n.hero-copy h1 { font-size: 2.4rem; margin: 10px 0; }\n.hero-copy p { font-size: 1.05rem; color: #dbeafe; line-height: 1.6; }\n.badge-row { display: flex; gap: 10px; flex-wrap: wrap; }\n.pill, .secondary-pill, .chip { display: inline-flex; align-items: center; gap: 6px; padding: 8px 12px; border-radius: 999px; background: rgba(255,255,255,0.12); color: #eff6ff; font-size: 0.9rem; }\n.hero-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-top: 16px; }\n.primary-btn { padding: 10px 16px; border-radius: 999px; background: linear-gradient(135deg, #38bdf8, #6366f1); color: white; font-weight: 700; }\n.stats-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }\n.stat-card, .panel, .module-card { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.14); border-radius: 18px; padding: 16px; backdrop-filter: blur(16px); }\n.stat-card { display: flex; gap: 10px; align-items: center; }\n.stat-card strong { display: block; font-size: 1.15rem; }\n.stat-card span { color: #dbeafe; font-size: 0.9rem; }\n.hero-visual { min-height: 280px; border-radius: 18px; overflow: hidden; background: radial-gradient(circle, rgba(56,189,248,0.22), rgba(7,19,37,0.75)); }\n.content-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-top: 18px; }\n.panel-title { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }\n.panel ul { padding-left: 18px; color: #dbeafe; line-height: 1.8; }\n.chip-stack { display: flex; flex-wrap: wrap; gap: 10px; }\n.modules-section { margin-top: 18px; }\n.module-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 12px; }\n.module-card h3 { margin: 10px 0 6px; }\n.module-card p { color: #dbeafe; line-height: 1.5; }\n.module-head { display: flex; justify-content: space-between; align-items: center; }\n.module-index { font-weight: 700; color: #7dd3fc; }\n.module-status { font-size: 0.8rem; color: #bbf7d0; text-transform: uppercase; letter-spacing: 0.06em; }\n.module-meta { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; color: #bfdbfe; font-size: 0.9rem; }\n@media (max-width: 900px) { .hero-card, .content-grid, .module-list { grid-template-columns: 1fr; } .hero-visual { min-height: 220px; } }\n",
            encoding="utf-8"
        )

    def _create_zip_bundle(self, course_root: Path, site_dir: Path) -> str:
        archive_path = course_root.parent / f"{course_root.name}.zip"
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path in site_dir.rglob('*'):
                if path.is_file():
                    zf.write(path, path.relative_to(site_dir))
        return str(archive_path)
