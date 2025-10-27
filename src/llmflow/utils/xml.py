# src/llmflow/utils/xml.py

from lxml import etree


def xpath_get(xml, xpath, namespaces=None):
    """
    Evaluate an XPath expression on a single XML string.
    Returns the first result, or list of results if multiple.
    """
    root = etree.fromstring(xml.encode("utf-8"))
    result = root.xpath(xpath, namespaces=namespaces)

    if isinstance(result, list):
        if len(result) == 1:
            return (
                result[0]
                if isinstance(result[0], str)
                else getattr(result[0], "text", None)
            )
        return [r if isinstance(r, str) else getattr(r, "text", None) for r in result]
    return result
