#!/usr/bin/env python3
"""
GUI launcher for Scripture Pipelines.

Starts the Flask backend server and optionally opens the browser.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path


def main():
    # Find the GUI backend directory
    gui_dir = Path(__file__).parent.parent / 'gui' / 'backend'

    if not gui_dir.exists():
        print("❌ GUI backend not found. Ensure llmflow[gui] is installed.")
        sys.exit(1)

    # Check if Flask is installed
    try:
        import flask
    except ImportError:
        print("❌ Flask not installed. Install with:")
        print("   pip install llmflow[gui]")
        sys.exit(1)

    print("🚀 Starting Scripture Pipelines GUI...")
    print()
    print("   Backend:  http://localhost:5000")
    print("   Frontend: (run separately with 'cd gui/frontend && npm run dev')")
    print()
    print("   Press Ctrl+C to stop")
    print()

    # Start Flask backend
    try:
        subprocess.run(
            [sys.executable, str(gui_dir / 'app.py')],
            cwd=str(gui_dir)
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")


if __name__ == '__main__':
    main()
