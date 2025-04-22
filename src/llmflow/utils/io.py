
import json
import re
import os
import unicodedata

def normalize_nfc(text):
    if isinstance(text, str):
        return unicodedata.normalize("NFC", text)
    elif isinstance(text, list):
        return [normalize_nfc(item) for item in text]
    else:
        return text

def write_nfc(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(normalize_nfc(content))

def sanitize_filename(text):
    return re.sub(r"[^\w]+", "_", text.strip())

def save_scene_list_json(passage, scenes):
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    safe_passage = sanitize_filename(passage)
    output_path = os.path.join(output_dir, f"scenes_{safe_passage}.json")

    # Ensure scenes is already a Python object (list/dict), not a JSON string
    if not isinstance(scenes, (list, dict)):
        raise TypeError("scenes must be a Python list or dictionary, not a JSON string")

    write_nfc(output_path, json.dumps(scenes, ensure_ascii=False, indent=2))
    return output_path

def write_exegetical_commentary(passage, content):
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    safe_passage = sanitize_filename(passage)
    output_path = os.path.join(output_dir, f"exegetical_pericope_{safe_passage}.md")

    write_nfc(output_path, content)
    return output_path

def save_leaders_guide(passage, intro, scenes, step1, step2, step3, step4, summary):
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    safe_passage = sanitize_filename(passage)
    output_path = os.path.join(output_dir, f"leaders_guide_{safe_passage}.md")

    lines = [intro.strip(), ""]
    for i, scene in enumerate(scenes):
        title = scene.get("Title", f"Scene {i+1}")
        citation = scene.get("Citation", "")
        text = scene.get("Berean Standard Bible", "")
        lines.append(f"## {title} ({citation})")
        if text:
            lines.append(f"*{text}*")
        lines.append("")
        lines.append(step1[i])
        lines.append("")
        lines.append(step2[i])
        lines.append("")
        lines.append(step3[i])
        lines.append("")
        lines.append(step4[i])
        lines.append("")
    lines.append(summary.strip())
    lines.append("")

    full_markdown = "\n".join(lines)
    write_nfc(output_path, full_markdown)
    return output_path
