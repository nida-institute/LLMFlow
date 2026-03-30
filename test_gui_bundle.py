#!/usr/bin/env python3
"""
Test script for the bundled GUI.

Verifies that the GUI can be built and launched correctly.
"""

import sys
from pathlib import Path


def test_build():
    """Test that build_gui.py completes successfully."""
    print("🧪 Testing GUI build...")

    import subprocess
    result = subprocess.run(
        [sys.executable, "build_gui.py"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Build failed:")
        print(result.stderr)
        return False

    print("✅ Build completed")
    return True


def test_static_files():
    """Verify static files were created."""
    print("\n🧪 Testing static files...")

    static_dir = Path("src/llmflow/gui/static")

    if not static_dir.exists():
        print(f"❌ Static directory not found: {static_dir}")
        return False

    index_html = static_dir / "index.html"
    if not index_html.exists():
        print(f"❌ index.html not found: {index_html}")
        return False

    assets_dir = static_dir / "assets"
    if not assets_dir.exists():
        print(f"❌ assets directory not found: {assets_dir}")
        return False

    print(f"✅ Static files present in {static_dir}")
    return True


def test_server_import():
    """Test that server module can be imported."""
    print("\n🧪 Testing server import...")

    try:
        from llmflow.gui.server import create_app, start_server
        print("✅ Server module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        return False


def test_gui_command():
    """Test that the GUI command is available."""
    print("\n🧪 Testing sp gui command...")

    import subprocess
    result = subprocess.run(
        ["sp", "gui", "--help"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ sp gui command failed:")
        print(result.stderr)
        return False

    if "--port" not in result.stdout or "--host" not in result.stdout:
        print(f"❌ sp gui command missing expected options")
        print(result.stdout)
        return False

    print("✅ sp gui command available")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Scripture Pipelines GUI - Bundle Test Suite")
    print("=" * 60)

    tests = [
        ("Build GUI", test_build),
        ("Static Files", test_static_files),
        ("Server Import", test_server_import),
        ("CLI Command", test_gui_command),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} raised exception: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10s} {name}")

    all_passed = all(success for _, success in results)

    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
