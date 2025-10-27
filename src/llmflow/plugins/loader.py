import importlib.util
import sys
from pathlib import Path

from llmflow.modules.logger import Logger

# Use unified logger
logger = Logger()

# Global plugin registry
plugin_registry = {}


def load_plugins():
    """Load all plugins from the plugins/contrib directory"""
    logger.info("🔌 Loading plugins...")

    plugins_dir = Path(__file__).parent / "contrib"

    if not plugins_dir.exists():
        logger.warning(f"Plugins directory not found: {plugins_dir}")
        return

    plugin_count = 0

    # Load all Python files in the contrib directory
    for plugin_file in plugins_dir.glob("*.py"):
        if plugin_file.name.startswith("__"):
            continue

        try:
            # Import the plugin module
            spec = importlib.util.spec_from_file_location(
                f"llmflow.plugins.contrib.{plugin_file.stem}", plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            logger.debug(f"Loaded plugin: {plugin_file.name}")
            plugin_count += 1

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_file.name}: {e}")

    logger.info(f"✅ Loaded {plugin_count} plugins")
    logger.debug(f"Available plugins: {list(plugin_registry.keys())}")


def register_plugin(name, func):
    """Register a plugin function"""
    plugin_registry[name] = func
    logger.debug(f"Registered plugin: {name}")


def get_plugin(name):
    """Get a plugin function by name"""
    return plugin_registry.get(name)


def list_plugins():
    """List all registered plugins"""
    return list(plugin_registry.keys())
