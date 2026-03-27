#!/usr/bin/env python3
"""
Discover and register projects and datasets from local directories.

Usage:
    python discover_and_register.py
"""
from pathlib import Path
from llmflow.registry import Registry
import yaml


def is_pipeline_project(path: Path) -> bool:
    """Check if directory contains pipeline files."""
    if not path.is_dir():
        return False

    # Look for pipeline YAML files
    for pattern in ["*.yaml", "*.yml"]:
        if list(path.glob(f"pipelines/{pattern}")) or list(path.glob(pattern)):
            return True

    return False


def get_project_description(path: Path) -> str:
    """Try to extract project description from README."""
    readme_files = ["README.md", "readme.md", "README.txt"]
    for readme in readme_files:
        readme_path = path / readme
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding='utf-8', errors='ignore')
                # Get first non-empty line
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                if lines:
                    # Skip markdown headers
                    first_line = lines[0].lstrip('#').strip()
                    return first_line[:100]  # Limit length
            except Exception:
                pass
    return ""


def discover_projects(base_path: Path, registry: Registry):
    """Discover and register projects in a directory."""
    if not base_path.exists():
        print(f"⚠️  Path not found: {base_path}")
        return

    print(f"\n🔍 Scanning for projects in {base_path}")
    registered = 0

    for item in base_path.iterdir():
        if not item.is_dir():
            continue

        # Skip hidden directories and common non-project dirs
        if item.name.startswith('.') or item.name in ['node_modules', '__pycache__', 'venv', '.venv']:
            continue

        if is_pipeline_project(item):
            project_name = item.name

            # Check if already registered
            if registry.projects.get(project_name) is not None:
                print(f"  ⏭️  {project_name} (already registered)")
                continue

            description = get_project_description(item)

            try:
                registry.projects.register(
                    name=project_name,
                    path=str(item.absolute()),
                    description=description
                )
                print(f"  ✅ {project_name}")
                registered += 1
            except Exception as e:
                print(f"  ❌ {project_name}: {e}")

    print(f"Registered {registered} new projects")


def is_dataset(path: Path) -> tuple[bool, str, str]:
    """
    Check if directory contains a dataset.

    Returns: (is_dataset, dataset_id, format)
    """
    if not path.is_dir():
        return False, "", ""

    name = path.name.lower()

    # Macula Greek patterns
    if 'macula' in name and 'greek' in name:
        # Check for lowfat XML files
        if (path / 'lowfat').exists() or list(path.glob('**/lowfat/*.xml')):
            return True, "macula-greek-lowfat", "xml"
        # Check for any Greek XML
        if list(path.glob('**/*.xml')):
            return True, f"macula-greek-{path.name}", "xml"

    # Macula Hebrew
    if 'macula' in name and 'hebrew' in name:
        if list(path.glob('**/*.xml')):
            return True, f"macula-hebrew-{path.name}", "xml"

    # Byzantine or Robinson-Pierpont text
    if 'byzantine' in name or 'robinson' in name or 'pierpont' in name or 'byztxt' in name:
        if list(path.glob('**/*.csv')) or list(path.glob('**/csv-unicode/*.csv')):
            return True, "byzantine-text-rp2018", "csv"

    # SDBH (Semantic Dictionary of Biblical Hebrew)
    if 'sdbh' in name:
        if list(path.glob('**/*.xml')) or list(path.glob('**/*.json')):
            fmt = "xml" if list(path.glob('**/*.xml')) else "json"
            return True, "sdbh-hebrew", fmt

    # LXX Greek
    if 'lxx' in name or 'septuagint' in name:
        if list(path.glob('**/*.xml')):
            return True, f"lxx-greek-{path.name}", "xml"

    # Check for large collections of biblical XML/CSV
    xml_count = len(list(path.glob('**/*.xml')))
    csv_count = len(list(path.glob('**/*.csv')))

    if xml_count > 20:  # Likely a Bible corpus
        return True, path.name, "xml"
    elif csv_count > 20:
        return True, path.name, "csv"

    return False, "", ""


def get_dataset_version(path: Path) -> str:
    """Try to extract version from path or README."""
    # Check for version in directory name
    name = path.name
    import re
    version_match = re.search(r'(\d{4}[-_]\d{2}[-_]\d{2}|\d+\.\d+|\d{4})', name)
    if version_match:
        return version_match.group(1)

    # Check README for version
    readme_path = path / "README.md"
    if readme_path.exists():
        try:
            content = readme_path.read_text(encoding='utf-8', errors='ignore')
            # Look for version patterns
            version_match = re.search(r'[Vv]ersion:?\s*(\d+\.\d+[\.\d]*|\d{4}[-_]\d{2}[-_]\d{2})', content)
            if version_match:
                return version_match.group(1)
        except Exception:
            pass

    return "unknown"


def discover_datasets(base_paths: list[Path], registry: Registry):
    """Discover and register datasets in directories."""
    print(f"\n🔍 Scanning for datasets")
    registered = 0

    for base_path in base_paths:
        if not base_path.exists():
            print(f"⚠️  Path not found: {base_path}")
            continue

        print(f"\nScanning {base_path}")

        for item in base_path.iterdir():
            if not item.is_dir():
                continue

            # Skip hidden directories
            if item.name.startswith('.'):
                continue

            is_ds, dataset_id, format_type = is_dataset(item)

            if is_ds:
                # Check if already registered
                if registry.datasets.exists(dataset_id):
                    print(f"  ⏭️  {dataset_id} (already registered)")
                    continue

                version = get_dataset_version(item)
                name = item.name.replace('-', ' ').replace('_', ' ').title()

                try:
                    registry.datasets.register(
                        id=dataset_id,
                        name=name,
                        path=str(item.absolute()),
                        version=version,
                        format=format_type
                    )
                    print(f"  ✅ {dataset_id} ({format_type}, v{version})")
                    registered += 1
                except Exception as e:
                    print(f"  ❌ {dataset_id}: {e}")

    print(f"\nRegistered {registered} new datasets")


def main():
    """Discover and register projects and datasets."""
    registry = Registry()

    print("=" * 60)
    print("Scripture Pipeline Registry Discovery")
    print("=" * 60)

    # Discover projects
    projects_base = Path.home() / "github" / "nida-institute"
    discover_projects(projects_base, registry)

    # Discover datasets
    dataset_bases = [
        Path.home() / "github" / "nida-institute",
        Path.home() / "github" / "biblical-humanities",
        Path.home() / "github" / "Clear",
        Path.home() / "github" / "BibleAquifer",
    ]
    discover_datasets(dataset_bases, registry)

    # Print summary
    print("\n" + "=" * 60)
    print("Registry Summary")
    print("=" * 60)
    print(f"Projects:  {len(registry.projects.list())}")
    print(f"Datasets:  {len(registry.datasets.list())}")
    print(f"Databases: {len(registry.databases.list())}")
    print(f"\nRegistry location: {registry.path}")
    print("\nRun 'sp registry list' to see all registered resources")


if __name__ == "__main__":
    main()
