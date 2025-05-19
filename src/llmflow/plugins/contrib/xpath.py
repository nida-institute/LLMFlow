# llmflow/plugins/contrib/xpath.py

from lxml import etree
from llmflow.plugins import register_plugin

def xpath_plugin(input_spec):
    path = input_spec["path"]
    xpath_expr = input_spec["xpath"]
    output_format = input_spec.get("output_format", "xml-string")

    with open(path, "rb") as f:
        tree = etree.parse(f)

    for node in tree.xpath(xpath_expr):
        if output_format == "xml-string":
            yield etree.tostring(node, encoding="unicode")
        elif output_format == "text":
            yield (node.text or "").strip()
        else:
            raise ValueError(f"Unsupported output_format: {output_format}")

register_plugin("xpath", xpath_plugin)

