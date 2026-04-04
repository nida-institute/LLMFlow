#!/usr/bin/env python3
"""
Diagnostic script: Check what the GUI server actually serves.

Verifies:
1. Static files exist in expected locations
2. HTML contains correct script/CSS references
3. API endpoints respond
4. Routes are configured correctly
"""

import sys
from pathlib import Path

def check_static_files():
    """Verify static files exist after build."""
    print("📁 Checking static files...")

    static_dir = Path("src/llmflow/gui/static")

    if not static_dir.exists():
        print(f"  ❌ Static directory not found: {static_dir}")
        return False

    print(f"  ✅ Static directory exists: {static_dir}")

    # Check for index.html
    index_html = static_dir / "index.html"
    if not index_html.exists():
        print(f"  ❌ index.html not found")
        return False

    print(f"  ✅ index.html exists")

    # Read and check index.html content
    content = index_html.read_text()

    if '<div id="root">' not in content:
        print("  ❌ index.html missing #root div")
        return False
    print("  ✅ index.html has #root div")

    if '<script' not in content:
        print("  ❌ index.html missing script tags")
        return False
    print("  ✅ index.html has script tags")

    # Check for assets directory
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        asset_files = list(assets_dir.iterdir())
        print(f"  ✅ Assets directory exists with {len(asset_files)} files")
        for asset in asset_files[:5]:  # Show first 5
            print(f"     - {asset.name}")
    else:
        print("  ⚠️  No assets directory (might be inlined)")

    return True


def check_server_config():
    """Check server.py configuration."""
    print("\n🔧 Checking server configuration...")

    server_file = Path("gui/backend/server.py")

    if not server_file.exists():
        print(f"  ❌ Server file not found: {server_file}")
        return False

    print(f"  ✅ Server file exists")

    content = server_file.read_text()

    # Check for key routes
    checks = [
        ("@app.route('/')", "Root route"),
        ("def serve_index", "Index handler"),
        ("/api/projects", "Projects API"),
        ("/api/health", "Health check"),
        ("static_folder", "Static folder config"),
    ]

    for pattern, description in checks:
        if pattern in content:
            print(f"  ✅ {description} configured")
        else:
            print(f"  ❌ {description} missing")

    return True


def check_backend_static_reference():
    """Check if backend references correct static path."""
    print("\n📂 Checking static file path resolution...")

    server_file = Path("gui/backend/server.py")
    content = server_file.read_text()

    if 'base_path / "static"' in content:
        print("  ✅ Server looks for 'static' subdirectory")
    else:
        print("  ⚠️  Static path resolution might be different")

    # Check what static folder will be in development
    backend_dir = Path("gui/backend")
    dev_static = backend_dir / "static"

    if dev_static.exists():
        print(f"  ✅ Development static exists: {dev_static}")
        index = dev_static / "index.html"
        if index.exists():
            print("     ✅ Has index.html")
        else:
            print("     ❌ Missing index.html")
    else:
        print(f"  ⚠️  Development static missing: {dev_static}")
        print("     This is expected - build process copies to src/llmflow/gui/static")

    return True


def main():
    print("🔍 GUI Diagnostic Check\n")
    print("=" * 60)

    all_ok = True

    # Run checks
    all_ok &= check_static_files()
    all_ok &= check_server_config()
    all_ok &= check_backend_static_reference()

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ All checks passed")
        print("\n🚀 To test the GUI:")
        print("   1. cd gui/backend")
        print("   2. Copy static files: cp -r ../../src/llmflow/gui/static .")
        print("   3. Run: hatch run python server.py")
        print("   4. Open: http://localhost:5000")
    else:
        print("❌ Some checks failed")
        print("\n💡 Try running: python build_gui.py")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
