from saxonche import PySaxonProcessor
from llmflow.modules.logger import Logger

logger = Logger()


def xslt_transform(stylesheet_path: str, xml_path: str = None, xml_string: str = None) -> str:
    logger.debug(f"xslt_transform called")
    logger.debug(f"  stylesheet_path: {stylesheet_path}")
    logger.debug(f"  xml_path: {xml_path}")
    logger.debug(f"  xml_string length: {len(xml_string) if xml_string else 0}")

    if not stylesheet_path:
        logger.debug("ERROR: stylesheet_path is empty or None")
        raise ValueError("stylesheet_path required")
    if not xml_path and not xml_string:
        logger.debug("ERROR: Both xml_path and xml_string are empty")
        raise ValueError("Provide xml_path or xml_string")

    input_type = 'file' if xml_path else 'string'
    logger.debug(f"Input type: {input_type}")

    with PySaxonProcessor(license=False) as proc:
        proc.set_cwd('.')
        xslt_proc = proc.new_xslt30_processor()

        logger.debug(f"Starting XSLT transformation...")
        if xml_path:
            result = xslt_proc.transform_to_string(
                stylesheet_file=stylesheet_path,
                source_file=xml_path
            )
        else:
            # For streaming: compile stylesheet, parse XML, then apply
            doc = proc.parse_xml(xml_text=xml_string)
            executable = xslt_proc.compile_stylesheet(stylesheet_file=stylesheet_path)
            result = executable.transform_to_string(xdm_node=doc)

        logger.debug(f"XSLT transform completed, output length: {len(result)} chars")
        return result


def run(**kwargs) -> str:
    """Wrapper that accepts kwargs from runner"""
    logger.debug(f"xslt_transform.run called with kwargs keys: {list(kwargs.keys())}")
    logger.debug(f"  Full kwargs: {kwargs}")

    stylesheet_path = kwargs.get('stylesheet_path')
    xml_path = kwargs.get('xml_path')
    xml_string = kwargs.get('xml_string')

    logger.debug(f"  stylesheet_path: {stylesheet_path}")
    logger.debug(f"  xml_path: {xml_path}")
    logger.debug(f"  xml_string present: {bool(xml_string)}")

    return xslt_transform(
        stylesheet_path=stylesheet_path,
        xml_path=xml_path,
        xml_string=xml_string
    )