#!/usr/bin/env python3
"""
GUI launcher for Scripture Pipelines.

Starts the bundled GUI server (Flask + static React frontend).
"""

import sys


def main():
    """Launch the GUI server."""
    try:
        from llmflow.gui.server import start_server
    except ImportError as e:
        print("❌ GUI dependencies not installed")
        print("   Install with: pip install llmflow[gui]")
        print(f"   Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to import GUI server: {e}")
        sys.exit(1)

    # Start server with default settings
    start_server(host='127.0.0.1', port=5000, open_browser=True)


if __name__ == '__main__':
    main()
