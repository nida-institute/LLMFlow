#!/usr/bin/env python3
"""
Test GUI endpoints to verify fixes work.

Tests:
1. /api/open-folder - Open Output button
2. /api/content/status - Content Lifecycle file selection
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:5050"

def test_open_folder():
    """Test the Open Output folder endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Open Output Folder")
    print("="*60)

    # Test with a real directory
    test_dir = Path.cwd()

    print(f"Testing with directory: {test_dir}")
    print(f"Directory exists: {test_dir.exists()}")

    response = requests.post(
        f"{BASE_URL}/api/open-folder",
        json={"path": str(test_dir)},
        headers={"Content-Type": "application/json"}
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("✅ PASS: Open folder endpoint works")
        return True
    else:
        print("❌ FAIL: Open folder endpoint failed")
        print(f"Error: {response.json()}")
        return False


def test_content_status():
    """Test the Content Lifecycle status endpoint."""
    print("\n" + "="*60)
    print("TEST 2: Content Lifecycle Status")
    print("="*60)

    # First get project path
    projects_response = requests.get(f"{BASE_URL}/api/projects")
    print(f"Projects response: {projects_response.status_code}")

    if projects_response.status_code != 200:
        print("❌ Cannot get projects list")
        return False

    projects_data = projects_response.json()
    print(f"Projects: {json.dumps(projects_data, indent=2)}")

    project_list = projects_data.get('projects', [])
    if not project_list:
        print("❌ No projects found")
        return False

    project = project_list[0]
    project_path = project.get('path')
    print(f"Using project: {project.get('name')} at {project_path}")

    # Check if content directory exists
    content_dir = Path(project_path) / 'content'
    print(f"Content directory: {content_dir}")
    print(f"Content directory exists: {content_dir.exists()}")

    if content_dir.exists():
        # List files in content directory
        print("\nFiles in content directory:")
        for stage_dir in content_dir.iterdir():
            if stage_dir.is_dir():
                print(f"  {stage_dir.name}/:")
                for file in stage_dir.iterdir():
                    if file.is_file():
                        print(f"    - {file.name}")

    # Test with a dummy file path
    test_file = "test-file"

    print(f"\nTesting content status for: {test_file}")

    response = requests.get(
        f"{BASE_URL}/api/content/status",
        params={
            "path": test_file,
            "project_path": project_path
        }
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    result = response.json()

    if response.status_code == 200 and result.get('success'):
        print("✅ PASS: Content status endpoint works")
        print(f"Stages returned: {len(result.get('stages', []))}")
        print(f"Authoritative stage: {result.get('authoritative_stage')}")
        return True
    else:
        print("❌ FAIL: Content status endpoint failed")
        print(f"Error: {result.get('error')}")
        return False


def test_content_config():
    """Test the Content Lifecycle config endpoint."""
    print("\n" + "="*60)
    print("TEST 3: Content Lifecycle Config")
    print("="*60)

    # Get project
    projects_response = requests.get(f"{BASE_URL}/api/projects")
    if projects_response.status_code != 200:
        print("❌ Cannot get projects list")
        return False

    projects_data = projects_response.json()
    project_list = projects_data.get('projects', [])
    if not project_list:
        print("❌ No projects found")
        return False

    project = project_list[0]
    project_path = project.get('path')

    print(f"Testing config for project: {project_path}")

    response = requests.get(
        f"{BASE_URL}/api/content/config",
        params={"project_path": project_path}
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    result = response.json()

    if response.status_code == 200 and result.get('success'):
        print("✅ PASS: Content config endpoint works")
        print(f"Stages: {[s['name'] for s in result.get('stages', [])]}")
        return True
    else:
        print("❌ FAIL: Content config endpoint failed")
        print(f"Error: {result.get('error')}")
        return False


if __name__ == "__main__":
    print("Testing GUI Endpoints")
    print("Make sure sp gui is running on port 5050")

    results = []

    try:
        results.append(("Open Folder", test_open_folder()))
        results.append(("Content Status", test_content_status()))
        results.append(("Content Config", test_content_config()))
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server at http://localhost:5050")
        print("Make sure 'sp gui' is running")
        exit(1)

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed")
        exit(1)
