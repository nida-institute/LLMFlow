"""Plugin loading and registration."""

import importlib
import pkgutil
from pathlib import Path

from llmflow.modules.logger import Logger

logger = Logger()

# Global plugin registry
plugin_registry = {}


def discover_plugins():
    """
    Discover and load all plugins from the plugins directory.

    Returns:
        dict: Plugin registry mapping plugin names to execute functions
    """
    logger.info("🔌 Loading plugins...")

    plugins_dir = Path(__file__).parent
    plugin_count = 0

    for finder, name, ispkg in pkgutil.iter_modules([str(plugins_dir)]):
        # Skip private modules and loader itself
        if name.startswith("_") or name == "loader":
            continue

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
