#!/usr/bin/env python3
"""
Token Optimizer Session Watcher Daemon

Watches for new Claude Code sessions and triggers auto-load automatically.
Monitors the ~/.claude/sessions/ directory for new session files.
"""

import os
import sys
import time
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add token-optimizer to path
sys.path.insert(0, str(Path(__file__).parent / "token-optimizer" / "skills" / "token-optimizer"))

from token_optimizer import (
    get_project_slug, get_memory_dir, load_session_state, save_session_state,
    auto_load_memories_if_needed
)


class SessionWatcher(FileSystemEventHandler):
    """Watches for new session files in ~/.claude/sessions/"""

    def __init__(self, cli_path: Path):
        self.cli_path = cli_path
        self.known_sessions = set()
        self.last_trigger = 0
        self.cooldown = 2  # seconds between triggers

    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)
        # Watch for new session JSON files
        if path.suffix == '.json' and 'session' in path.name.lower():
            self.check_and_trigger(path)

    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix == '.json' and 'session' in path.name.lower():
            self.check_and_trigger(path)

    def check_and_trigger(self, session_file: Path):
        """Check if this is a new session and trigger auto-load."""
        now = time.time()
        if now - self.last_trigger < self.cooldown:
            return

        try:
            # Read session file to get project info
            with open(session_file) as f:
                session_data = json.load(f)

            project_slug = session_data.get('project', {}).get('slug') or session_data.get('project_slug')
            if not project_slug:
                # Try to infer from working directory
                cwd = session_data.get('cwd') or session_data.get('working_directory')
                if cwd:
                    project_slug = Path(cwd).name.lower().replace(" ", "-").replace("_", "-")

            if project_slug:
                print(f"[{datetime.now().isoformat()}] New session detected for project: {project_slug}")
                self.trigger_auto_load(project_slug)
                self.last_trigger = now

        except Exception as e:
            print(f"Error processing session file: {e}")

    def trigger_auto_load(self, project_slug: str):
        """Trigger auto-load for the project."""
        try:
            # Run the CLI load command for the project
            env = os.environ.copy()
            env['TOKEN_OPTIMIZER_PROJECT'] = project_slug

            result = subprocess.run(
                [sys.executable, str(self.cli_path), "load"],
                env=env,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"  ✅ Auto-loaded memories for {project_slug}")
                if result.stdout.strip():
                    print(f"  {result.stdout.strip()}")
            else:
                print(f"  ⚠️  Auto-load failed: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Auto-load timed out")
        except Exception as e:
            print(f"  ❌ Auto-load error: {e}")


def find_sessions_dir() -> Path:
    """Find the Claude sessions directory."""
    candidates = [
        Path.home() / ".claude" / "sessions",
        Path.home() / "Library" / "Application Support" / "Claude-3p" / "local-agent-mode-sessions",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def main():
    sessions_dir = find_sessions_dir()
    cli_path = Path(__file__).parent / "token-optimizer" / "skills" / "token-optimizer" / "token_optimizer.py"

    if not cli_path.exists():
        print(f"❌ CLI not found at {cli_path}")
        sys.exit(1)

    print(f"🔍 Token Optimizer Session Watcher")
    print(f"   Watching: {sessions_dir}")
    print(f"   CLI: {cli_path}")
    print(f"   Started: {datetime.now().isoformat()}")
    print("   Press Ctrl+C to stop")

    if not sessions_dir.exists():
        print(f"⚠️  Sessions directory not found: {sessions_dir}")
        print("   Creating it...")
        sessions_dir.mkdir(parents=True, exist_ok=True)

    event_handler = SessionWatcher(cli_path)
    observer = Observer()
    observer.schedule(event_handler, str(sessions_dir), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping watcher...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
