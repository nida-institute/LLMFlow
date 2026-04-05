#!/usr/bin/env python3
"""
Build script for Scripture Pipelines GUI.

This script:
1. Builds the React frontend to static files
2. Copies built assets to the package directory
3. Prepares for bundling with nuitka

Run this before packaging with nuitka.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    # Get paths
    script_dir = Path(__file__).parent
    frontend_dir = script_dir / "gui" / "frontend"
    package_gui_dir = script_dir / "src" / "llmflow" / "gui"
    static_dir = package_gui_dir / "static"

    print("[BUILD] Building Scripture Pipelines GUI...")
    print(f"   Frontend: {frontend_dir}")
    print(f"   Output:   {static_dir}")

    # Check if frontend directory exists
    if not frontend_dir.exists():
        print(f"[ERROR] Frontend directory not found: {frontend_dir}")
        sys.exit(1)

    # Check if node_modules exists - use npm ci in CI for clean install
    if not (frontend_dir / "node_modules").exists():
        npm_cmd = "ci" if os.getenv("CI") else "install"
        print(f"\n[INSTALL] Installing npm dependencies (npm {npm_cmd})...")
        result = subprocess.run(
            ["npm", npm_cmd],
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"[ERROR] npm {npm_cmd} failed:")
            print(result.stderr)
            sys.exit(1)
        print("[OK] npm dependencies installed")

    # Build frontend
    print("\n[BUILD] Building React frontend (production)...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"[ERROR] npm build failed:")
        print(result.stderr)
        sys.exit(1)
    print("[OK] Frontend build complete")

    # Check if dist directory was created
    dist_dir = frontend_dir / "dist"
    if not dist_dir.exists():
        print(f"[ERROR] Build output not found: {dist_dir}")
        sys.exit(1)

    # Create package gui directory if it doesn't exist
    package_gui_dir.mkdir(parents=True, exist_ok=True)

    # Remove old static directory if it exists
    if static_dir.exists():
        print(f"\n[CLEAN] Removing old static files...")
        shutil.rmtree(static_dir)

    # Copy dist to static
    print(f"\n[COPY] Copying static files to package...")
    shutil.copytree(dist_dir, static_dir)
    print(f"[OK] Static files copied to {static_dir}")

    # Copy server.py to package
    server_src = script_dir / "gui" / "backend" / "server.py"
    server_dst = package_gui_dir / "server.py"
    if server_src.exists():
        shutil.copy2(server_src, server_dst)
        print(f"[OK] Server copied to {server_dst}")
    else:
        print(f"[WARN] server.py not found at {server_src}")

    # Copy executor.py to package
    executor_src = script_dir / "gui" / "backend" / "executor.py"
    executor_dst = package_gui_dir / "executor.py"
    if executor_src.exists():
        shutil.copy2(executor_src, executor_dst)
        print(f"[OK] Executor copied to {executor_dst}")
    else:
        print(f"[WARN] executor.py not found at {executor_src}")

    # Create __init__.py if it doesn't exist
    init_file = package_gui_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Scripture Pipelines GUI components."""\n')
        print(f"[OK] Created {init_file}")

    print("\n[OK] GUI build complete!")
    print(f"\n   Static files: {static_dir}")
    print(f"   Server:       {server_dst}")
    print("\n   Ready for nuitka bundling.")


if __name__ == "__main__":
    main()
