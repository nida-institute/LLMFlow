"""Plugin to mechanically insert references into markdown entry structure."""

import json
import re
from typing import Dict, Any
from llmflow.modules.logger import Logger

logger = Logger()


def execute(step_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLMflow plugin entry point - mechanically insert references.

    Args:
        step_config: Dictionary with 'inputs' key containing lemma, sense_structure, reference_analysis

    Returns:
        Dictionary with 'entry_with_examples' key containing markdown string
    """
    # Support both nested inputs and flat config
    if "inputs" in step_config:
        config = step_config["inputs"]
    else:
        config = step_config

    lemma = config.get('lemma', '')
    sense_structure = config.get('sense_structure', '')
    reference_analysis = config.get('reference_analysis', '')

    if not all([lemma, sense_structure, reference_analysis]):
        raise ValueError("Missing required inputs: lemma, sense_structure, or reference_analysis")

    logger.info(f"Inserting references for lemma: {lemma}")

    markdown = insert_references(lemma, sense_structure, reference_analysis)

    return {
        'entry_with_examples': markdown
    }


def extract_json_from_text(text: str) -> str:
    """Extract JSON from text that may have markdown fences or extra content."""
    if isinstance(text, dict):
        return text

    # Try to find JSON in markdown code fences
    json_fence_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_fence_match:
        return json_fence_match.group(1)

    # Try to find JSON in plain code fences
    code_fence_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_fence_match:
        return code_fence_match.group(1)

    # Try to find raw JSON (starts with { and ends with })
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)

    # Return as-is and let json.loads fail with better error
    return text


def insert_references(
    lemma: str,
    sense_structure: Any,
    reference_analysis: Any
) -> str:
    """
    Mechanically insert all references into their assigned senses.

    This is deterministic data transformation - no LLM needed.
    """
    # Handle both dict and JSON string inputs
    if isinstance(sense_structure, str):
        structure = json.loads(sense_structure)
    else:
        structure = sense_structure

    # Handle reference_analysis - may have markdown fences or malformed JSON
    if isinstance(reference_analysis, str):
        cleaned = extract_json_from_text(reference_analysis)
        try:
            refs_data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse reference_analysis JSON")
            logger.error(f"Error: {e}")
            logger.error(f"First 500 chars of cleaned text: {cleaned[:500]}")
            logger.error(f"Last 500 chars of cleaned text: {cleaned[-500:]}")

            # Save the malformed JSON for inspection
            debug_file = f"debug_{lemma}_references_malformed.json"
            with open(debug_file, 'w') as f:
                f.write(reference_analysis)
            logger.error(f"Full malformed JSON saved to: {debug_file}")
            raise ValueError(f"Malformed JSON in reference_analysis. See {debug_file} for details.") from e
    else:
        refs_data = reference_analysis

    # Create lookup table: ID → reference data
    ref_lookup = {ref['id']: ref for ref in refs_data['references']}

    total_refs = len(refs_data['references'])
    logger.info(f"Processing {total_refs} references from analysis")

    # Build markdown
    lines = [f"# {lemma}", ""]

    def process_sense(sense: Dict[str, Any], level: int = 2) -> None:
        """Recursively process a sense and its subsenses."""
        # Sense header
        header_prefix = "#" * level
        sense_path = sense.get('path', '')
        sense_label = sense.get('label', '')
        lines.append(f"{header_prefix} {sense_path}. {sense_label}")
        lines.append("")

        # Sense definition
        if sense.get('definition'):
            lines.append(sense['definition'])
            lines.append("")

        # Get references for this sense
        ref_ids = sense.get('reference_ids', [])

        if ref_ids:
            lines.append("**References:**")

            for ref_id in sorted(ref_ids):
                if ref_id not in ref_lookup:
                    logger.error(f"Reference ID {ref_id} not found in analysis")
                    lines.append(f"- **ERROR**: Reference ID {ref_id} not found in analysis")
                    continue

                ref = ref_lookup[ref_id]

                # Build reference line
                citation = ref['reference']
                greek = ref.get('sblgnt_extracted', '')
                translation = ref.get('translation', '')

                # Check if this needs an EDITOR note
                needs_review = ref.get('needs_review', False)

                if needs_review:
                    # Show EDITOR note in blockquote format
                    lines.append(f"- **{citation}**: {greek} / \"{translation}\"")
                    lines.append(f"  > **EDITOR:** Abbott-Smith cited this reference but didn't quote the text. Greek extracted from SBLGNT.")
                else:
                    # Normal reference (Abbott-Smith quoted it)
                    lines.append(f"- **{citation}**: {greek} / \"{translation}\"")

            lines.append("")
        else:
            lines.append("No references for this sense.")
            lines.append("")

        # Process subsenses recursively
        for subsense in sense.get('subsenses', []):
            process_sense(subsense, level + 1)

    # Process all top-level senses
    for sense in structure.get('senses', []):
        process_sense(sense)

    inserted_count = sum(len(s.get('reference_ids', [])) for s in structure.get('senses', []))
    logger.info(f"Inserted {inserted_count}/{total_refs} references into markdown")

    return "\n".join(lines)


def register():
    """Register the insert_references plugin."""
    return {
        "insert_references": execute
    }