#!/usr/bin/env python3
"""
CLI script for cinematic video production pipeline.
Usage: python scripts/video_pipeline.py --story "..." --style cinematic_realism --output /path/to/output
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.modes import VideoProductionPipeline
from backend.config import settings


async def main():
    parser = argparse.ArgumentParser(description="Run the cinematic video production pipeline")
    parser.add_argument("--story", "-s", required=True, help="Story concept or path to story file")
    parser.add_argument("--style", "-t", default="cinematic_realism",
                        choices=VideoProductionPipeline.SUB_STYLES,
                        help="Visual style")
    parser.add_argument("--output", "-o", default=None, help="Output directory")
    args = parser.parse_args()

    story = args.story
    if Path(story).exists():
        story = Path(story).read_text(encoding="utf-8")

    print(f"[Video Pipeline] Style: {args.style}")
    print(f"[Video Pipeline] Story: {story[:60]}...")

    blueprint = {
        "story": story,
        "style": args.style
    }

    pipeline = VideoProductionPipeline()
    result = await pipeline.run(blueprint)

    print(f"\n[✓] Video pipeline generated!")
    print(f"    Project: {result['project_path']}")
    print(f"    Shots: {result['shots_count']}")
    print(f"    Files: {', '.join(result['files'])}")
    print(f"\nNext: Run video_prompts.json through Pruna P-Video for actual rendering.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
