#!/usr/bin/env python3
"""
CLI script for automated course creation.
Usage: python scripts/course_generator.py --blueprint path/to/blueprint.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.modes import CourseCreationPipeline
from backend.config import settings


async def main():
    parser = argparse.ArgumentParser(description="Generate a course from a blueprint file")
    parser.add_argument("--blueprint", "-b", required=True, help="Path to blueprint JSON file")
    parser.add_argument("--output", "-o", default=None, help="Output directory (overrides config)")
    args = parser.parse_args()

    bp_path = Path(args.blueprint)
    if not bp_path.exists():
        print(f"Error: Blueprint not found: {bp_path}")
        sys.exit(1)

    with open(bp_path, "r") as f:
        blueprint = json.load(f)

    print(f"[Course Generator] Loading blueprint: {blueprint.get('title', 'Untitled')}")
    print(f"[Course Generator] Modules: {len(blueprint.get('modules', []))}")

    pipeline = CourseCreationPipeline()
    result = await pipeline.run(blueprint)

    print(f"\n[✓] Course generated successfully!")
    print(f"    Path: {result['course_path']}")
    print(f"    Modules: {result['modules_count']}")
    print(f"    Manifest: {result['course_path']}/manifest.json")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
