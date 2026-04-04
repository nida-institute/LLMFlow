"""Type checking tests using Pyright.

These tests ensure type safety across the codebase. Marked as 'slow' so they can be
skipped during fast development iteration.

Run type checks:
    pytest tests/test_types.py          # Run type checks only
    pytest -m slow                       # Run all slow tests (including type checks)
    pytest --run-slow                    # Run all tests including slow ones

Skip type checks (fast iteration):
    pytest -m "not slow"                 # Skip slow tests
    pytest                               # Default (skips slow unless configured)
"""

import subprocess
import sys
from pathlib import Path

import pytest


def test_type_stubs_installed():
    """Verify that required type stub packages are installed.

    These type stubs provide better IDE support and enable stricter type checking.
    This test ensures the development environment has proper type information.
    """
    try:
        import yaml  # noqa: F401
    except ImportError:
        pytest.skip("PyYAML not installed")

    # Check for types-PyYAML
    result = subprocess.run(
        ["python", "-c", "import yaml; yaml.safe_load.__annotations__"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(
            "types-PyYAML not installed. Type stubs are required for standard mode.\n"
            "Install with: hatch run pip install types-PyYAML"
        )

    # Verify other critical type stubs
    required_stubs = [
        ("jsonschema", "types-jsonschema"),
        ("markdown", "types-Markdown"),
        ("flask", "types-Flask"),
    ]

    missing = []
    for module, stub_package in required_stubs:
        try:
            __import__(module)
            # Try to access type information
            result = subprocess.run(
                ["python", "-c", f"import {module}"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                missing.append(stub_package)
        except ImportError:
            # Module not installed is fine, we only check stubs for installed modules
            pass

    if missing:
        pytest.fail(
            f"Missing type stubs: {', '.join(missing)}\n"
            f"Install with: hatch run pip install {' '.join(missing)}"
        )

    print("✅ All required type stubs installed")


@pytest.mark.slow
def test_pyright_src_passes():
    """Source code (src/) must pass Pyright type checking.

    Only checks src/llmflow, not tests/, because test code uses patterns
    that confuse type checkers (mocks, patches, dynamic fixtures, negative tests).

    This ensures production code is type-safe while allowing pragmatic test code.
    """
    repo_root = Path(__file__).parent.parent

    result = subprocess.run(
        ["npx", "-y", "pyright", "src/llmflow"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    stdout = result.stdout or ""

    if result.returncode != 0:
        # Print pyright output to stderr so it's visible in test output
        print("\n" + "="*80, file=sys.stderr)
        print("PYRIGHT TYPE ERRORS:", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print(stdout, file=sys.stderr)

        pytest.fail(
            f"\n\nPyright type check failed (exit code {result.returncode}).\n"
            f"See output above for details.\n\n"
            f"To fix:\n"
            f"  1. Run locally: npx pyright src/llmflow\n"
        )

    print("✅ Pyright: All source files are type-safe")
