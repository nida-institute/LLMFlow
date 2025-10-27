from lxml import etree

from llmflow.plugins import register_plugin  # ✅ must import this!


def xpath_plugin(input_spec):
    path = input_spec["path"]
    xpath_expr = input_spec["xpath"]
    output_format = input_spec.get("output_format", "xml-string")
    nsmap = input_spec.get("namespaces", {})  # <--- new

    with open(path, "rb") as f:
        tree = etree.parse(f)

    nodes = tree.xpath(xpath_expr, namespaces=nsmap)

    for node in nodes:
        if output_format == "xml-string":
            yield etree.tostring(node, encoding="unicode")
        elif output_format == "text":
            yield (node.text or "").strip()
        else:
            raise ValueError(f"Unsupported output_format: {output_format}")


# ✅ This must be called at module level
register_plugin("xpath", xpath_plugin)
