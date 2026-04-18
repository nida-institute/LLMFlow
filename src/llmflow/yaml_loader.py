"""Shared YAML loader with LLMFlow tag support.

Imported by both runner.py and linter.py to parse pipeline files that use
tags such as !window_advance.  Keeping this in its own module avoids circular
imports between runner and linter.
"""
import yaml


class LLMFlowLoader(yaml.SafeLoader):
    """SafeLoader extended to recognise LLMFlow YAML tags.

    Tagged list items are parsed as normal mappings with an extra ``_tag``
    key set to the tag name.  For example::

        - !window_advance
          name: advance
          cursor: next_pos
          step: ...

    becomes ``{"_tag": "window_advance", "name": "advance", ...}``.
    """


def _tagged_mapping_constructor(tag_name: str):
    def constructor(loader, node):
        data = loader.construct_mapping(node, deep=True)
        data["_tag"] = tag_name
        return data
    return constructor


LLMFlowLoader.add_constructor("!window_advance", _tagged_mapping_constructor("window_advance"))
