"""XPath plugin for extracting data from XML files."""

from lxml import etree
from llmflow.modules.logger import Logger

logger = Logger()


def execute(step_config):
    """Execute XPath query on XML file."""
    # Support both nested inputs and flat config
    if "inputs" in step_config:
        config = step_config["inputs"]
    else:
        config = step_config

    path = config.get("path") or config.get("from")
    if not path:
        raise ValueError("xpath requires 'path' or 'from' key")

    xpath_expr = config["xpath"]
    namespaces = config.get("namespaces", {})
    output_format = config.get("output_format", "xml-string")

    tree = etree.parse(str(path))
    results = tree.xpath(xpath_expr, namespaces=namespaces)

    for elem in results:
        if output_format == "text":
            # FIX: Handle both elements and attribute results
            if isinstance(elem, str):  # Attribute value
                yield elem
            elif hasattr(elem, 'text'):  # Element
                yield elem.text or ""
            else:
                yield str(elem)  # Fallback
        else:
            yield etree.tostring(elem, encoding="unicode")


def register():
    """Register the xpath plugin."""
    return {
        "xpath": execute
    }
