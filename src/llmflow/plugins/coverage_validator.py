"""Coverage validator plugin for ensuring all Abbott-Smith references are accounted for."""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

from llmflow.modules.logger import Logger

logger = Logger()


def extract_reference_details(base_json: Dict) -> List[Dict]:
    """
    Walk the base_json structure and extract all references with full context.
    Returns list of dicts with: {ref, path, pattern, greek_text, gloss, markdown}
    """
    references = []

    for sense in base_json.get("senses", []):
        sense_path = sense.get("path", "")

        def walk_subsenses(subsenses, parent_path):
            for subsense in subsenses:
                sub_path = subsense.get("path", parent_path)

                # Extract references from usage groups
                for usage_group in subsense.get("usageGroups", []):
                    ug_path = usage_group.get("path", sub_path)
                    markdown = usage_group.get("markdown", "")

                    # Infer pattern from context
                    pattern = "general"
                    if "distributive" in markdown.lower():
                        pattern = "distributive"
                    elif "narrative" in markdown.lower() or "narration" in markdown.lower():
                        pattern = "narrative"
                    elif "quoted" in markdown.lower() or "aratus" in markdown.lower():
                        pattern = "quoted"

                    # Extract Greek text and glosses from content items
                    greek_phrases = []
                    glosses = []

                    for content_item in usage_group.get("content", []):
                        if content_item.get("type") == "foreign":
                            greek_phrases.append(content_item.get("text", ""))
                        elif content_item.get("type") == "gloss":
                            glosses.append(content_item.get("text", ""))
                        elif content_item.get("type") == "reference":
                            ref = content_item.get("reference", "")
                            if ref:
                                references.append({
                                    "ref": ref,
                                    "path": ug_path,
                                    "pattern": pattern,
                                    "greek_text": " ".join(greek_phrases) if greek_phrases else "",
                                    "gloss": " ".join(glosses) if glosses else "",
                                    "markdown": markdown,
                                    "subsense_label": subsense.get("label", ""),
                                    "sense_id": sense.get("id", "")
                                })

                # Recurse into nested subsenses
                if "subsenses" in subsense:
                    walk_subsenses(subsense["subsenses"], sub_path)

        # Process top-level subsenses
        if "subsenses" in sense:
            walk_subsenses(sense["subsenses"], sense_path)

        # Also check direct usage groups at sense level
        for usage_group in sense.get("usageGroups", []):
            ug_path = usage_group.get("path", sense_path)
            markdown = usage_group.get("markdown", "")

            pattern = "general"
            if "distributive" in markdown.lower():
                pattern = "distributive"
            elif "narrative" in markdown.lower() or "narration" in markdown.lower():
                pattern = "narrative"

            greek_phrases = []
            glosses = []

            for content_item in usage_group.get("content", []):
                if content_item.get("type") == "foreign":
                    greek_phrases.append(content_item.get("text", ""))
                elif content_item.get("type") == "gloss":
                    glosses.append(content_item.get("text", ""))
                elif content_item.get("type") == "reference":
                    ref = content_item.get("reference", "")
                    if ref:
                        references.append({
                            "ref": ref,
                            "path": ug_path,
                            "pattern": pattern,
                            "greek_text": " ".join(greek_phrases) if greek_phrases else "",
                            "gloss": " ".join(glosses) if glosses else "",
                            "markdown": markdown,
                            "subsense_label": "",
                            "sense_id": sense.get("id", "")
                        })

    return references


def get_covered_references(evidence_json: Dict) -> Set[str]:
    """Extract all references that are covered in evidence_json."""
    covered = set()

    # From retained examples
    for ref in evidence_json.get("base_coverage", {}).get("retained_examples", []):
        covered.add(ref)

    # From transformed examples
    for item in evidence_json.get("base_coverage", {}).get("transformed_examples", []):
        covered.add(item.get("ref", ""))

    # From missing examples
    for item in evidence_json.get("base_coverage", {}).get("missing_examples", []):
        covered.add(item.get("ref", ""))

    # From sense group examples
    for sense_group in evidence_json.get("sense_groups", []):
        for example in sense_group.get("examples", []):
            covered.add(example.get("ref", ""))

    return {r for r in covered if r}


def execute(step_config: Dict) -> str:
    """
    Validate coverage and enrich evidence.json with missing Abbott-Smith references.

    Args:
        step_config: Dictionary containing:
            - inputs: Dict with:
                - base_json: Base JSON data (or string)
                - evidence_json: Evidence JSON data (or string)

    Returns:
        Updated evidence.json as JSON string
    """
    inputs = step_config.get("inputs", {})

    # Get base_json - may be dict or JSON string
    base_json_input = inputs.get("base_json", "")
    if isinstance(base_json_input, str):
        base_json = json.loads(base_json_input)
    else:
        base_json = base_json_input

    # Get evidence_json - may be dict or JSON string
    evidence_json_input = inputs.get("evidence_json", "")
    if isinstance(evidence_json_input, str):
        evidence_json = json.loads(evidence_json_input)
    else:
        evidence_json = evidence_json_input

    logger.info("Analyzing coverage...")    # Extract all references with full context
    all_ref_details = extract_reference_details(base_json)
    covered_refs = get_covered_references(evidence_json)

    logger.info(f"Found {len(all_ref_details)} total references in base.json")
    logger.info(f"Found {len(covered_refs)} covered references in evidence.json")

    # Find missing references
    missing_ref_details = [r for r in all_ref_details if r["ref"] not in covered_refs]

    if not missing_ref_details:
        logger.info("✓ All references accounted for!")
        return json.dumps(evidence_json, indent=2, ensure_ascii=False)

    logger.info(f"⚠ {len(missing_ref_details)} references not accounted for")

    # Add missing references with full context
    missing_examples = evidence_json.setdefault("base_coverage", {}).setdefault("missing_examples", [])
    existing_missing = {item["ref"] for item in missing_examples}

    for ref_detail in missing_ref_details:
        ref = ref_detail["ref"]
        if ref not in existing_missing:
            logger.info(f"  + Adding {ref} from Abbott-Smith")
            missing_examples.append({
                "ref": ref,
                "pattern": ref_detail["pattern"],
                "greek_text": ref_detail["greek_text"],
                "gloss": ref_detail["gloss"],
                "reason": "Not found in initial gather pass",
                "note": f"Path: {ref_detail['path']}. Context: {ref_detail['markdown'][:100]}",
                "source": "Abbott-Smith (retained by coverage validator)"
            })

            # Update usage_group_audit
            evidence_json.setdefault("usage_group_audit", []).append({
                "path": ref_detail["path"],
                "status": "retained",
                "covered_by": "missing_examples",
                "references": [ref],
                "note": f"Added by coverage validator - {ref_detail['pattern']} pattern"
            })

    # Update counts
    self_audit = evidence_json.setdefault("self_audit", {})
    retained = len(evidence_json.get("base_coverage", {}).get("retained_examples", []))
    transformed = len(evidence_json.get("base_coverage", {}).get("transformed_examples", []))
    missing = len(missing_examples)
    total = retained + transformed + missing

    self_audit.update({
        "base_reference_count": total,
        "retained_count": retained,
        "transformed_count": transformed,
        "missing_count": missing
    })

    # Update method_notes
    method_notes = evidence_json.setdefault("method_notes", [])
    coverage_note = f"coverage: retained {retained} + missing {missing} = {total} total references from Abbott-Smith"

    if method_notes and method_notes[0].startswith("coverage:"):
        method_notes[0] = coverage_note
    else:
        method_notes.insert(0, coverage_note)

    if len(method_notes) < 2:
        method_notes.append("Coverage validator restored missing Abbott-Smith references with full context.")

    logger.info(f"✓ Coverage complete: {retained} retained + {missing} added = {total} total")

    return json.dumps(evidence_json, indent=2, ensure_ascii=False)


def register():
    """Register the coverage_validator plugin."""
    return {
        "coverage_validator": execute
    }
