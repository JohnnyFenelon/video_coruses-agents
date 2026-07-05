#!/usr/bin/env python3
"""
Johnny Agents — AI Orchestration Engine
Startup launcher for both backend API server and development tools.
"""
import sys
import os
import webbrowser
from pathlib import Path


def main():
    print("""
+==========================================+
|        Johnny Agents v3.0.0              |
|    AI Orchestration Engine               |
+==========================================+
    """)

    # Ensure we're in the project root
    os.chdir(Path(__file__).parent)

    mode = sys.argv[1] if len(sys.argv) > 1 else "server"

    if mode == "server" or mode == "all":
        print("[+] Starting API server on http://localhost:3000")
        print("[+] Frontend UI at http://localhost:3000")
        print("[+] Open browser automatically...")
        
        # Start server
        from backend.main import start
        webbrowser.open("http://localhost:3000")
        start()

    elif mode == "init":
        print("[+] Initializing project structure...")
        from backend.config import settings
        print(f"[+] Config at: {settings._data.__class__}")
        print("[✓] Ready. Add your API keys in Settings or edit config.json directly.")

    elif mode == "blueprint":
        from scripts.course_generator import main as course_main
        import asyncio
        asyncio.run(course_main())

    elif mode == "video":
        from scripts.video_pipeline import main as video_main
        import asyncio
        asyncio.run(video_main())

    else:
        print(f"Usage: python run.py [server|init|blueprint|video]")
        print(f"  server    - Start the web UI and API server (default)")
        print(f"  init      - Initialize config and directories")
        print(f"  blueprint - Run course generator CLI (requires --blueprint)")
        print(f"  video     - Run video pipeline CLI (requires --story)")


if __name__ == "__main__":
    main()
