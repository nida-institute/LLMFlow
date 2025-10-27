# plugins/__init__.py

plugin_registry = {}


def register_plugin(name, func):
    if name in plugin_registry:
        raise ValueError(f"Plugin '{name}' is already registered")
    plugin_registry[name] = func
