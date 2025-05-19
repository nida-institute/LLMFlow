import os
import importlib
import logging
from llmflow.plugins import plugin_registry

def load_plugins():
    plugin_base = "llmflow.plugins.contrib"
    plugin_dir = os.path.join(os.path.dirname(__file__), "contrib")

    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            modulename = f"{plugin_base}.{filename[:-3]}"
            try:
                before = set(plugin_registry.keys())
                importlib.import_module(modulename)
                after = set(plugin_registry.keys())
                new_plugins = after - before

                if not new_plugins:
                    logging.warning(f"Plugin module '{modulename}' did not register anything.")
                else:
                    logging.debug(f"Registered plugin(s) {sorted(new_plugins)} from '{modulename}'")

            except Exception as e:
                logging.warning(f"Failed to load plugin '{modulename}': {e}")
