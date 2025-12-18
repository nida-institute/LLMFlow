"""Plugin loading and registration."""

import importlib
import pkgutil
from pathlib import Path

from llmflow.modules.logger import Logger
from llmflow.plugins.tsv_reader import execute as tsv_execute

logger = Logger()

# Global plugin registry
plugin_registry = {
    "tsv": tsv_execute,
    "csv": tsv_execute,  # CSV uses same reader
}


def discover_plugins():
    """
    Discover and load all plugins from the plugins directory.

    Returns:
        dict: Plugin registry mapping plugin names to execute functions
    """
    logger.info("🔌 Loading plugins...")

    # List of known plugin modules (hardcoded for PyInstaller compatibility)
    known_plugins = [
        "coverage_validator",
        "echo",
        "insert_references",
        "xml_entry_to_base_json",
        "xpath",
        "xslt_transform",
    ]

    plugin_count = 0

    for name in known_plugins:
        try:
            # Import the plugin module
            module = importlib.import_module(f"llmflow.plugins.{name}")

            # If it has a register() function, call it
            if hasattr(module, "register"):
                registered = module.register()
                plugin_registry.update(registered)
                plugin_count += len(registered)
                logger.debug(f"Loaded plugin: {name} ({list(registered.keys())})")

        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")

    logger.info(f"✅ Loaded {plugin_count} plugin(s)")
    logger.debug(f"Available plugins: {list(plugin_registry.keys())}")

    return plugin_registry


def get_plugin(name):
    """Get a plugin function by name"""
    return plugin_registry.get(name)


def list_plugins():
    """List all registered plugins"""
    return list(plugin_registry.keys())


# Load plugins on module import
discover_plugins()
