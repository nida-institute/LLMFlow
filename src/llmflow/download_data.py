"""Download biblical datasets for use in LLMFlow pipelines."""
import os
import shutil
import sys
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

from llmflow.modules.logger import Logger

logger = Logger()

AWESOME_BIBLICAL_DATA_URL = "https://github.com/nida-institute/awesome-biblical-data"

# Built-in catalog. Any dataset from the awesome-biblical-data list can be added here.
CATALOG: dict[str, dict] = {
    "macula-greek": {
        "repo": "Clear-Bible/macula-greek",
        "branch": "main",
        "license": "CC BY 4.0",
        "description": "Macula Greek NT (Lowfat XML, Node XML, TSV morphology)",
        "approx_size": "~150MB",
    },
    "macula-hebrew": {
        "repo": "Clear-Bible/macula-hebrew",
        "branch": "main",
        "license": "CC BY 4.0",
        "description": "Macula Hebrew OT (XML, TSV morphology)",
        "approx_size": "~400MB",
    },
    "berean-usx": {
        "repo": "Freely-Given-org/OpenEnglishBible",
        "branch": "main",
        "license": "CC BY-SA 4.0",
        "description": "Berean Standard Bible in USX format",
        "approx_size": "~15MB",
    },
}


def get_default_data_dir() -> Path:
    """Return the base data directory, honouring LLMFLOW_DATA_DIR env var."""
    env = os.environ.get("LLMFLOW_DATA_DIR")
    if env:
        return Path(env)
    return Path.home() / ".sp" / "data"


def run_download_data(
    dataset: str | None = None,
    dest: str | None = None,
    list_only: bool = False,
) -> None:
    if list_only:
        _show_catalog()
        return

    if dataset is None:
        _show_usage_hint()
        return

    if dataset not in CATALOG:
        logger.error(f"❌ Unknown dataset: '{dataset}'")
        logger.error("   Run 'sp download-data --list' to see available datasets.")
        logger.error(f"   Or see {AWESOME_BIBLICAL_DATA_URL} for the full catalog.")
        sys.exit(1)

    entry = CATALOG[dataset]
    base = Path(dest) if dest else get_default_data_dir()
    dest_path = base / dataset
    _download_dataset(dataset, entry, dest_path)


def _show_usage_hint() -> None:
    print("sp download-data: Download biblical reference datasets\n")
    print("Usage:")
    print("  sp download-data --list                    List available datasets")
    print("  sp download-data <dataset>                 Download to ~/.sp/data/<dataset>/")
    print("  sp download-data <dataset> --dest <path>   Download to custom path\n")
    print("Set LLMFLOW_DATA_DIR to change the default base directory.\n")
    _show_catalog()


def _show_catalog() -> None:
    print(f"Available datasets (full catalog: {AWESOME_BIBLICAL_DATA_URL}):\n")
    print(f"  {'Dataset':<22} {'Size':<10} {'License':<16} Description")
    print(f"  {'-'*22} {'-'*10} {'-'*16} {'-'*40}")
    for name, entry in CATALOG.items():
        print(
            f"  {name:<22} {entry['approx_size']:<10} {entry['license']:<16} {entry['description']}"
        )


def _download_dataset(name: str, entry: dict, dest: Path) -> None:
    if dest.exists():
        logger.info(f"✅ Dataset '{name}' already exists at {dest}")
        logger.info("   Use --dest to download to a different location.")
        return

    repo = entry["repo"]
    branch = entry.get("branch", "main")
    url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"

    logger.info(f"📥 Downloading {name} ({entry['approx_size']}) from {repo}...")
    logger.info(f"   Destination: {dest}")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "llmflow/sp"})
        with urllib.request.urlopen(req) as response:
            data = response.read()
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        sys.exit(1)

    logger.info("📦 Extracting...")
    try:
        dest.mkdir(parents=True, exist_ok=True)
        repo_basename = repo.split("/")[-1]
        prefix = f"{repo_basename}-{branch}/"
        with zipfile.ZipFile(BytesIO(data)) as zf:
            for member in zf.infolist():
                if member.filename.startswith(prefix):
                    member.filename = member.filename[len(prefix):]
                    if member.filename:
                        zf.extract(member, dest)
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        shutil.rmtree(dest, ignore_errors=True)
        sys.exit(1)

    logger.info(f"✅ Downloaded '{name}' to {dest}")
    logger.info(f"   Reference in pipelines: ${{LLMFLOW_DATA_DIR}}/{name}/...")
    logger.info(f"   Tip: export LLMFLOW_DATA_DIR={dest.parent}")
