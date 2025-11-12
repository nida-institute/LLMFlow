import xml.etree.ElementTree as ET
import unicodedata
import re
from llmflow.modules.logger import Logger

logger = Logger()


def xml_entry_to_base_json(entry_xml: str) -> dict:
    logger.debug(f"xml_entry_to_base_json called with XML length: {len(entry_xml)} chars")

    root = ET.fromstring(entry_xml)
    ns = {'tei': root.tag.split('}')[0].strip('{')}
    entry_key = root.get('key')

    logger.debug(f"Parsing entry with key: '{entry_key}'")

    # Store the raw XML snippet
    xml_snippet = entry_xml

    segments = []
    transforms = []
    senses = []
    forms = []
    incomplete_segments = []
    groups = []
    warnings = []
    notes = []

    seg_index = [0]  # Use list to make it mutable in nested functions

    def normalize_greek(text: str) -> tuple:
        """Normalize Greek text to NFC and track if changed"""
        normalized = unicodedata.normalize('NFC', text)
        if normalized != text:
            return normalized, {"type": "normalization", "from": text, "to": normalized}
        return normalized, None

    def check_pattern_flags(foreign_text: str, all_foreign_in_group: list) -> list:
        """Check for generic pattern flags"""
        flags = []

        # pairedContrast: contains both μέν and δέ
        all_text = ' '.join(all_foreign_in_group)
        if 'μέν' in all_text and 'δέ' in all_text:
            flags.append('pairedContrast')

        # endsWithInfinitiveStem
        if foreign_text.endswith('ειν'):
            flags.append('endsWithInfinitiveStem')

        # neuterPluralPlusGenitive
        if foreign_text.startswith('τὰ '):
            if 'τοῦ' in foreign_text or 'τῆς' in foreign_text:
                flags.append('neuterPluralPlusGenitive')

        # genitiveChain
        if any(foreign_text.endswith(end) for end in ['τοῦ', 'τῆς', 'τῶν']):
            flags.append('genitiveChain')

        # kinshipGenitive
        if foreign_text.startswith('ὁ τοῦ'):
            flags.append('kinshipGenitive')

        # domainGenitive
        if foreign_text.startswith('τὰ τοῦ'):
            flags.append('domainGenitive')

        # abstractDomainGenitive
        if foreign_text.startswith('τὰ τῆς'):
            flags.append('abstractDomainGenitive')

        return flags

    def check_incomplete(foreign_text: str) -> bool:
        """Check if foreign segment is incomplete (ends with article/genitive)"""
        return any(foreign_text.endswith(end) for end in ['τοῦ', 'τῆς', 'τῶν', 'ὁ', 'ἡ', 'τό'])

    def check_semantic_concerns(gloss: str, foreign: str) -> list:
        """Check for semantic concerns (possessives without morphology)"""
        concerns = []
        if gloss.startswith('his ') or gloss.startswith('her '):
            # Heuristic: check if Greek has possessive αὐτοῦ, αὐτῆς, etc.
            if 'αὐτοῦ' not in foreign and 'αὐτῆς' not in foreign:
                concerns.append({
                    "type": "possessiveWithoutMorphology",
                    "gloss": gloss,
                    "foreign": foreign
                })
        return concerns

    def tokenize_text(text: str) -> list:
        """Tokenize plain text into prose and punctuation segments"""
        tokens = []
        # Split on punctuation but keep it
        parts = re.split(r'([,;.])', text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part in [',', ';', '.']:
                tokens.append({
                    "index": seg_index[0],
                    "type": "punct",
                    "text": part
                })
            else:
                tokens.append({
                    "index": seg_index[0],
                    "type": "senseProse",
                    "text": part
                })
            seg_index[0] += 1
        return tokens

    def process_sense_recursive(sense_elem, parent_path=""):
        """Recursively process sense elements to maintain hierarchy"""
        sense_n = (sense_elem.get('n') or '').strip()

        # Build sense path by combining parent path with current n
        if parent_path and sense_n:
            sense_path = f"{parent_path}.{sense_n}"
        elif sense_n:
            sense_path = sense_n
        else:
            sense_path = parent_path

        sense_start_index = seg_index[0]

        logger.debug(f"  Processing sense '{sense_path}'")

        # Process direct children (not nested senses)
        for child in sense_elem:
            tag = child.tag.split('}')[-1]

            # Skip nested sense elements - they'll be processed recursively
            if tag == 'sense':
                continue

            text = (child.text or '').strip()

            if tag == 'foreign':
                # Foreign text
                normalized, transform = normalize_greek(text)
                is_incomplete = check_incomplete(text)

                seg = {
                    "index": seg_index[0],
                    "type": "foreign",
                    "text": text,
                    "normalizedForm": normalized,
                    "sensePath": sense_path
                }
                if is_incomplete:
                    seg["status"] = "incomplete"

                # Add xml:lang if present
                lang = child.get('{http://www.w3.org/XML/1998/namespace}lang')
                if lang:
                    seg["lang"] = lang

                segments.append(seg)
                if transform:
                    transforms.append(transform)
                seg_index[0] += 1

            elif tag == 'gloss':
                # Gloss
                seg = {
                    "index": seg_index[0],
                    "type": "gloss",
                    "text": text,
                    "sensePath": sense_path
                }
                segments.append(seg)
                seg_index[0] += 1

            elif tag == 'ref':
                # Reference
                osis_ref = child.get('osisRef')
                seg = {
                    "index": seg_index[0],
                    "type": "ref",
                    "osisRef": osis_ref,
                    "sensePath": sense_path
                }
                if text:
                    seg["text"] = text
                segments.append(seg)
                seg_index[0] += 1

            elif tag in ['hi', 'emph', 'note', 'cit']:
                # Process nested content as prose
                inner_text = ''.join(child.itertext()).strip()
                if inner_text:
                    prose_tokens = tokenize_text(inner_text)
                    for tok in prose_tokens:
                        tok["sensePath"] = sense_path
                    segments.extend(prose_tokens)

            else:
                # Plain text or other elements - tokenize
                if text:
                    prose_tokens = tokenize_text(text)
                    for tok in prose_tokens:
                        tok["sensePath"] = sense_path
                    segments.extend(prose_tokens)

            # Check for tail text after element
            if child.tail:
                tail = child.tail.strip()
                if tail:
                    prose_tokens = tokenize_text(tail)
                    for tok in prose_tokens:
                        tok["sensePath"] = sense_path
                    segments.extend(prose_tokens)

        # Record sense with its segment range (before processing nested senses)
        sense_end_before_nested = seg_index[0]

        # Now process nested sense elements recursively
        for child in sense_elem:
            tag = child.tag.split('}')[-1]
            if tag == 'sense':
                process_sense_recursive(child, sense_path)

        # Record this sense
        senses.append({
            "sensePath": sense_path,
            "segmentIndices": list(range(sense_start_index, sense_end_before_nested))
        })

        logger.debug(f"    Sense '{sense_path}': {sense_end_before_nested - sense_start_index} direct segments")

    # Find all top-level sense elements (direct children of entry)
    for sense in root.findall('./tei:sense', ns):
        process_sense_recursive(sense)

    # Build groups and forms from segments
    logger.debug(f"Building groups from {len(segments)} segments")

    current_group = None
    current_group_segments = []
    group_id = 1
    form_id = 1
    incomplete_id = 1

    for seg in segments:
        if seg["type"] == "foreign":
            # Start new group if we have a previous one
            if current_group:
                # Finalize previous group
                groups.append(current_group)

                # Create form or incomplete segment
                foreign_list = [s["text"] for s in current_group_segments if s["type"] == "foreign"]
                primary_foreign = foreign_list[0] if foreign_list else ""
                normalized_primary = [s["normalizedForm"] for s in current_group_segments if s["type"] == "foreign"][0] if foreign_list else ""
                glosses = [s["text"] for s in current_group_segments if s["type"] == "gloss"]
                refs = [s["osisRef"] for s in current_group_segments if s["type"] == "ref"]

                is_incomplete = any(s.get("status") == "incomplete" for s in current_group_segments if s["type"] == "foreign")
                pattern_flags = check_pattern_flags(primary_foreign, foreign_list)

                source_indices = [s["index"] for s in current_group_segments]

                if is_incomplete:
                    incomplete_segments.append({
                        "id": f"incomplete_{incomplete_id}",
                        "sensePath": current_group["sensePath"],
                        "rawForeign": primary_foreign,
                        "normalizedForeign": normalized_primary,
                        "glosses": glosses,
                        "refs": refs,
                        "patternFlags": pattern_flags,
                        "authoritySources": ["Abbott-Smith"] if not refs else [],
                        "reason": "unreferencedInSource" if not refs else "incompletePhrase",
                        "sourceIndices": source_indices
                    })
                    incomplete_id += 1
                else:
                    semantic_concerns = []
                    if glosses and foreign_list:
                        semantic_concerns = check_semantic_concerns(glosses[0], primary_foreign)

                    forms.append({
                        "id": f"form_{form_id}",
                        "sensePath": current_group["sensePath"],
                        "rawForeignList": foreign_list,
                        "normalizedPrimary": normalized_primary,
                        "glosses": glosses,
                        "refs": refs,
                        "punctuationTrail": current_group.get("terminator", ""),
                        "patternFlags": pattern_flags,
                        "authoritySources": ["Abbott-Smith"] if not refs else [],
                        "semanticConcerns": semantic_concerns,
                        "sourceIndices": source_indices,
                        "annotations": {},
                        "demoOrigin": False
                    })
                    form_id += 1

            # Start new group
            current_group = {
                "id": f"g{group_id}",
                "sensePath": seg.get("sensePath", ""),
                "segmentRange": [seg["index"], seg["index"]],
                "foreignPrimary": seg["text"]
            }
            current_group_segments = [seg]
            group_id += 1

        elif seg["type"] in ["punct"] and seg["text"] in [';', '.']:
            # Terminator - end current group
            if current_group:
                current_group["segmentRange"][1] = seg["index"]
                current_group["terminator"] = seg["text"]
                groups.append(current_group)

                # Create form or incomplete segment (same logic as above)
                foreign_list = [s["text"] for s in current_group_segments if s["type"] == "foreign"]
                if foreign_list:
                    primary_foreign = foreign_list[0]
                    normalized_primary = [s["normalizedForm"] for s in current_group_segments if s["type"] == "foreign"][0]
                    glosses = [s["text"] for s in current_group_segments if s["type"] == "gloss"]
                    refs = [s["osisRef"] for s in current_group_segments if s["type"] == "ref"]

                    is_incomplete = any(s.get("status") == "incomplete" for s in current_group_segments if s["type"] == "foreign")
                    pattern_flags = check_pattern_flags(primary_foreign, foreign_list)
                    source_indices = [s["index"] for s in current_group_segments]

                    if is_incomplete:
                        incomplete_segments.append({
                            "id": f"incomplete_{incomplete_id}",
                            "sensePath": current_group["sensePath"],
                            "rawForeign": primary_foreign,
                            "normalizedForeign": normalized_primary,
                            "glosses": glosses,
                            "refs": refs,
                            "patternFlags": pattern_flags,
                            "authoritySources": ["Abbott-Smith"] if not refs else [],
                            "reason": "unreferencedInSource" if not refs else "incompletePhrase",
                            "sourceIndices": source_indices
                        })
                        incomplete_id += 1
                    else:
                        semantic_concerns = []
                        if glosses:
                            semantic_concerns = check_semantic_concerns(glosses[0], primary_foreign)

                        forms.append({
                            "id": f"form_{form_id}",
                            "sensePath": current_group["sensePath"],
                            "rawForeignList": foreign_list,
                            "normalizedPrimary": normalized_primary,
                            "glosses": glosses,
                            "refs": refs,
                            "punctuationTrail": seg["text"],
                            "patternFlags": pattern_flags,
                            "authoritySources": ["Abbott-Smith"] if not refs else [],
                            "semanticConcerns": semantic_concerns,
                            "sourceIndices": source_indices,
                            "annotations": {},
                            "demoOrigin": False
                        })
                        form_id += 1

                current_group = None
                current_group_segments = []

        else:
            # Add to current group
            if current_group:
                current_group["segmentRange"][1] = seg["index"]
                current_group_segments.append(seg)

    # Handle final group if not terminated
    if current_group:
        groups.append(current_group)
        foreign_list = [s["text"] for s in current_group_segments if s["type"] == "foreign"]
        if foreign_list:
            primary_foreign = foreign_list[0]
            normalized_primary = [s["normalizedForm"] for s in current_group_segments if s["type"] == "foreign"][0]
            glosses = [s["text"] for s in current_group_segments if s["type"] == "gloss"]
            refs = [s["osisRef"] for s in current_group_segments if s["type"] == "ref"]

            is_incomplete = any(s.get("status") == "incomplete" for s in current_group_segments if s["type"] == "foreign")
            pattern_flags = check_pattern_flags(primary_foreign, foreign_list)
            source_indices = [s["index"] for s in current_group_segments]

            if is_incomplete:
                incomplete_segments.append({
                    "id": f"incomplete_{incomplete_id}",
                    "sensePath": current_group["sensePath"],
                    "rawForeign": primary_foreign,
                    "normalizedForeign": normalized_primary,
                    "glosses": glosses,
                    "refs": refs,
                    "patternFlags": pattern_flags,
                    "authoritySources": ["Abbott-Smith"] if not refs else [],
                    "reason": "unreferencedInSource" if not refs else "incompletePhrase",
                    "sourceIndices": source_indices
                })
            else:
                semantic_concerns = []
                if glosses:
                    semantic_concerns = check_semantic_concerns(glosses[0], primary_foreign)

                forms.append({
                    "id": f"form_{form_id}",
                    "sensePath": current_group["sensePath"],
                    "rawForeignList": foreign_list,
                    "normalizedPrimary": normalized_primary,
                    "glosses": glosses,
                    "refs": refs,
                    "punctuationTrail": current_group.get("terminator", ""),
                    "patternFlags": pattern_flags,
                    "authoritySources": ["Abbott-Smith"] if not refs else [],
                    "semanticConcerns": semantic_concerns,
                    "sourceIndices": source_indices,
                    "annotations": {},
                    "demoOrigin": False
                })

    logger.debug(f"Result: {len(segments)} segments, {len(groups)} groups, {len(forms)} forms, {len(incomplete_segments)} incomplete")

    return {
        "lemma": entry_key,
        "schemaVersion": "base.v4.structural",
        "rawEntry": {
            "xmlSnippet": xml_snippet,
            "segments": segments,
            "transforms": transforms
        },
        "senses": senses,
        "forms": forms,
        "incompleteSegments": incomplete_segments,
        "groups": groups,
        "warnings": warnings,
        "notes": notes
    }


def run(**kwargs) -> dict:
    """Wrapper that accepts kwargs from runner"""
    logger.debug(f"xml_entry_to_base_json.run called with kwargs: {list(kwargs.keys())}")
    entry_xml = kwargs.get('entry_xml')
    logger.debug(f"  entry_xml length: {len(entry_xml) if entry_xml else 0} chars")

    result = xml_entry_to_base_json(entry_xml)
    logger.debug(f"Returning dict with {len(result.get('segments', []))} segments")
    return result