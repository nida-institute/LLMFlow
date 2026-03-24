"""sp load-db — load a downloaded dataset into a database backend.

Drivers are registered via register_driver(). Only 'basex' is built-in;
additional drivers (postgres, couchdb, etc.) can be registered at import time
by plugins.

Usage:
    sp load-db basex macula-greek
    sp load-db basex acai --force
    sp load-db basex acai --name my_acai --source /path/to/data
    sp load-db --list-drivers
"""
import subprocess
import sys
from pathlib import Path
from typing import Callable

from llmflow.download_data import CATALOG, get_default_data_dir
from llmflow.modules.logger import Logger

logger = Logger()

# ---------------------------------------------------------------------------
# Driver registry
# ---------------------------------------------------------------------------

_DRIVERS: dict[str, Callable] = {}


def register_driver(name: str, fn: Callable) -> None:
    """Register a load-db driver by name."""
    _DRIVERS[name] = fn


def list_drivers() -> list[str]:
    return sorted(_DRIVERS.keys())


# ---------------------------------------------------------------------------
# BaseX driver
# ---------------------------------------------------------------------------

def _load_basex(source: Path, db_name: str, force: bool) -> None:
    """Load *source* directory into a BaseX database named *db_name*."""
    try:
        subprocess.run(["basex", "-c", "nothing"], capture_output=True, check=False)
    except FileNotFoundError:
        logger.error("❌ basex not found on PATH")
        logger.error("   💡 Tip: Install BaseX and ensure 'basex' is executable")
        sys.exit(1)

    if force:
        logger.info(f"🗑️  Dropping existing database '{db_name}' (--force)...")
        result = subprocess.run(
            ["basex", "-c", f"DROP DB {db_name}"],
            capture_output=True,
            text=True,
        )
        # Ignore "database not found" errors — that's fine on first run
        if result.returncode != 0 and "not found" not in result.stderr.lower():
            logger.error(f"❌ Failed to drop database: {result.stderr.strip()}")
            sys.exit(1)

    logger.info(f"📦 Loading '{source}' into BaseX database '{db_name}'...")
    result = subprocess.run(
        ["basex", "-c", f"CREATE DB {db_name} {source}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"❌ BaseX load failed: {result.stderr.strip()}")
        sys.exit(1)

    logger.info(f"✅ Database '{db_name}' is ready.")


register_driver("basex", _load_basex)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_load_db(
    driver: str | None,
    dataset: str | None,
    db_name: str | None = None,
    force: bool = False,
    source: str | None = None,
    list_drivers_only: bool = False,
) -> None:
    if list_drivers_only:
        logger.info("Available load-db drivers:")
        for d in list_drivers():
            logger.info(f"  {d}")
        return

    if driver is None:
        logger.error("❌ driver is required  (e.g. sp load-db basex acai)")
        logger.error("   💡 Tip: run 'sp load-db --list-drivers' to see available drivers")
        sys.exit(1)

    if driver not in _DRIVERS:
        logger.error(f"❌ Unknown driver '{driver}'")
        logger.error(f"   Available: {', '.join(list_drivers()) or 'none'}")
        sys.exit(1)

    if dataset is None:
        logger.error("❌ dataset is required  (e.g. sp load-db basex acai)")
        sys.exit(1)

    # Resolve source path
    if source is not None:
        source_path = Path(source)
    else:
        source_path = get_default_data_dir() / dataset

    if not source_path.exists():
        logger.error(f"❌ Data directory not found: {source_path}")
        if dataset in CATALOG:
            logger.error(f"   💡 Tip: run 'sp download-data {dataset}' first")
        sys.exit(1)

    resolved_db_name = db_name if db_name else dataset

    _DRIVERS[driver](source_path, resolved_db_name, force)
