
import json
import re
import os
import unicodedata

def normalize_nfc(text):
    return unicodedata.normalize("NFC", text)

def sanitize_filename(text):
    return re.sub(r"[^\w]+", "_", text.strip())

def save_scene_list_json(passage, scenes):
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    safe_passage = sanitize_filename(passage)
    output_path = os.path.join(output_dir, f"leaders_guide_{safe_passage}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scenes, f, ensure_ascii=False, indent=2)
    return output_path
