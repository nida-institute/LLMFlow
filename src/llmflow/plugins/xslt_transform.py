"""XSLT transformation plugin for LLMFlow"""

from pathlib import Path
from llmflow.modules.logger import Logger

logger = Logger()


def execute(config: dict) -> str:
    """Execute XSLT transformation using Saxon for XSLT 3.0 support"""
    try:
        from saxonche import PySaxonProcessor
    except ImportError:
        raise ImportError("saxonche is required for XSLT 3.0. Install with: pip install saxonche")

    # Support both nested inputs and flat config
    if "inputs" in config:
        inputs = config["inputs"]
    else:
        inputs = config

    stylesheet_path = inputs.get("stylesheet_path")
    xml_string = inputs.get("xml_string")
    xml_path = inputs.get("xml_path")

    if not stylesheet_path:
        raise ValueError("xslt_transform requires 'stylesheet_path'")

    if not xml_string and not xml_path:
        raise ValueError("xslt_transform requires either 'xml_string' or 'xml_path'")

    logger.debug(f"🔧 Using Saxon XSLT 3.0 processor")
    logger.debug(f"🔧 Loading XSLT stylesheet: {stylesheet_path}")

    xslt_path = Path(stylesheet_path)
    if not xslt_path.exists():
        raise FileNotFoundError(f"XSLT stylesheet not found: {stylesheet_path}")

    # Initialize Saxon processor
    with PySaxonProcessor(license=False) as proc:
        xslt_processor = proc.new_xslt30_processor()

        # Compile stylesheet
        try:
            executable = xslt_processor.compile_stylesheet(stylesheet_file=str(xslt_path))
        except Exception as e:
            logger.error(f"❌ Failed to compile XSLT stylesheet: {e}")
            raise

        # Transform
        logger.debug("🔧 Applying XSLT transformation...")
        try:
            if xml_string:
                logger.debug(f"🔧 Parsing XML string (length: {len(xml_string)})")
                result = executable.transform_to_string(xdm_node=proc.parse_xml(xml_text=xml_string))
            else:
                logger.debug(f"🔧 Loading XML from: {xml_path}")
                result = executable.transform_to_string(source_file=str(xml_path))

        except Exception as e:
            logger.error(f"❌ XSLT transformation failed: {e}")
            raise

    # Debug logging
    logger.debug(f"🔧 Transform result length: {len(result)}")
    logger.debug(f"🔧 First 200 chars: {result[:200]}")

    if result.strip().startswith('{') or result.strip().startswith('['):
        logger.info("✅ Transform output appears to be proper JSON")

    return result


def register():
    """Register the xslt plugin."""
    return {
        "xslt": execute
    }