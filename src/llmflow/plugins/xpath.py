"""XPath plugin for extracting data from XML files."""

from lxml import etree
from llmflow.modules.logger import Logger

logger = Logger()


def execute(step_config):
    """
    Execute XPath query on XML file.

    Args:
        step_config: Dictionary containing:
            - path: Path to XML file
            - xpath: XPath expression (already resolved by runner)
            - namespaces: Optional namespace mappings
            - output_format: 'text' or 'xml-string' (default: 'xml-string')

    Returns:
        Generator yielding extracted data
    """
    path = step_config["path"]
    xpath_expr = step_config["xpath"]
    output_format = step_config.get("output_format", "xml-string")
    nsmap = step_config.get("namespaces", {})

    logger.debug(f"XPath plugin received path: {path}")
    logger.debug(f"XPath plugin received expression: {xpath_expr}")
    logger.debug(f"Namespaces: {nsmap}")

    with open(path, "rb") as f:
        tree = etree.parse(f)

    nodes = tree.xpath(xpath_expr, namespaces=nsmap)

    logger.debug(f"XPath returned {len(nodes)} results")

    if not nodes:
        logger.error(f"XPath query returned no results for expression: {xpath_expr}")
        logger.error(f"Querying file: {path}")
        return  # Generator returns empty

    for i, node in enumerate(nodes):
        if output_format == "xml-string":
            if hasattr(node, 'tag'):
                result = etree.tostring(node, encoding="unicode")
                logger.debug(f"Result {i}: element <{node.tag}> ({len(result)} chars)")
                yield result
            else:
                result = str(node)
                logger.debug(f"Result {i}: string/attribute ({len(result)} chars)")
                yield result
        elif output_format == "text":
            if hasattr(node, 'text'):
                result = (node.text or "").strip()
                logger.debug(f"Result {i}: text from <{node.tag}> ({len(result)} chars)")
                yield result
            else:
                result = str(node).strip()
                logger.debug(f"Result {i}: string value ({len(result)} chars)")
                yield result
        else:
            raise ValueError(f"Unsupported output_format: {output_format}")


def register():
    """Register the xpath plugin."""
    return {
        "xpath": execute
    }
