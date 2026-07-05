from pathlib import Path

from backend.modes.course_creation import CourseCreationPipeline


def test_react_course_site_bundle_contains_rich_ui_assets(tmp_path: Path) -> None:
    pipeline = CourseCreationPipeline()
    course_root = tmp_path / "demo_course"
    site_dir = course_root / "site"

    manifest = {
        "title": "Intro to AI",
        "topic": "Artificial Intelligence",
        "audience": "beginners",
        "difficulty": "beginner",
        "learning_objectives": ["Understand AI basics"],
        "modules": [
            {"slug": "intro", "title": "What is AI?", "status": "generated"},
        ],
    }
    modules = [{"slug": "intro", "title": "What is AI?", "status": "generated"}]

    pipeline._build_react_site(course_root, site_dir, manifest, modules)

    package_json = (site_dir / "package.json").read_text(encoding="utf-8")
    app_jsx = (site_dir / "src" / "App.jsx").read_text(encoding="utf-8")

    assert (site_dir / "package.json").exists()
    assert (site_dir / "src" / "App.jsx").exists()
    assert "lucide-react" in package_json
    assert "three" in package_json
    assert "Canvas" in app_jsx
    assert "emoji" in app_jsx.lower()
