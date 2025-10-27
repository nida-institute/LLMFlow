#!/usr/bin/env python3
"""Run all tests with coverage"""

import os
import subprocess
import sys


def run_tests():
    """Run pytest with coverage"""
    # Add src to Python path
    src_path = os.path.join(os.path.dirname(__file__), "src")
    os.environ["PYTHONPATH"] = src_path

    cmd = [
        "pytest",
        "-v",
        "--cov=llmflow",
        "--cov-report=html",
        "--cov-report=term-missing",
        "tests/",
    ]

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
