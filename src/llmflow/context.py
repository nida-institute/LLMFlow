"""AI Context file discovery and management."""

import re
from pathlib import Path
from typing import Dict, List


def extract_description(content: str, max_length: int = 100) -> str:
    """
    Extract a brief description from markdown content.

    Tries to extract from:
    1. First paragraph after first heading
    2. First non-empty line if no heading
    3. Heading text itself if no paragraph follows

    Args:
        content: Markdown file content
        max_length: Maximum length of description (will truncate with ...)

    Returns:
        Brief description string
    """
    if not content or not content.strip():
        return ""

    lines = content.split("\n")

    # Skip HTML comments and empty lines at start
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith("<!--") and line:
            break
        i += 1

    if i >= len(lines):
        return ""

    # Look for first heading
    heading = None
    first_paragraph = None

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and comments
        if not line or line.startswith("<!--"):
            i += 1
            continue

        # Found a heading
        if line.startswith("#"):
            heading = re.sub(r"^#+\s*", "", line)
            i += 1

            # Look for first paragraph after heading
            while i < len(lines):
                para_line = lines[i].strip()
                if not para_line or para_line.startswith("<!--"):
                    i += 1
                    continue
                if not para_line.startswith("#"):
                    first_paragraph = para_line
                    break
                break
            break
        else:
            # No heading, use first non-empty line
            first_paragraph = line
            break

    # Choose description
    description = first_paragraph or heading or ""

    # Truncate if too long
    if len(description) > max_length:
        description = description[:max_length].rstrip() + "..."

    return description


def list_context_files(base_path: Path) -> List[Dict[str, str]]:
    """
    List all AI context files in docs/ai-context/ directory.

    Args:
        base_path: Project root directory

    Returns:
        List of dicts with 'file' and 'description' keys, sorted alphabetically
    """
    ai_context_dir = Path(base_path) / "docs" / "ai-context"

    if not ai_context_dir.exists() or not ai_context_dir.is_dir():
        return []

    result = []

    # Find all .md files (top-level only, no subdirectories)
    for md_file in ai_context_dir.glob("*.md"):
        if md_file.is_file():
            content = md_file.read_text(encoding="utf-8")
            description = extract_description(content)

            result.append({
                "file": md_file.name,
                "description": description
            })

    # Sort alphabetically by filename
    result.sort(key=lambda x: x["file"])

    return result


def format_context_list(context_files: List[Dict[str, str]]) -> str:
    """
    Format context files list for display to user.

    Args:
        context_files: List from list_context_files()

    Returns:
        Formatted string for terminal output
    """
    if not context_files:
        return "No AI context files found in docs/ai-context/\n\nRun 'sp init' to create initial context files."

    lines = ["AI Context Files in docs/ai-context/:\n"]

    # Calculate max filename length for alignment
    max_len = max(len(item["file"]) for item in context_files)

    for item in context_files:
        filename = item["file"]
        description = item["description"] or "(no description)"
        lines.append(f"  {filename:<{max_len}}  {description}")

    return "\n".join(lines)


def generate_context_inventory(base_path: Path) -> str:
    """
    Generate brief inventory of AI context files for injection into AI system prompts.

    This is used by pipeline execution to inform AI about available documentation.

    Args:
        base_path: Project root directory

    Returns:
        Brief text describing available context files
    """
    context_files = list_context_files(base_path)

    if not context_files:
        return ""

    lines = [
        "AI Context Available in docs/ai-context/:",
        ""
    ]

    for item in context_files:
        desc = f" ({item['description']})" if item['description'] else ""
        lines.append(f"- {item['file']}{desc}")

    lines.append("")
    lines.append("Read these files for project conventions before asking user.")

    return "\n".join(lines)
