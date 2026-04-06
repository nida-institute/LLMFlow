#!/usr/bin/env python3
"""
Update copilot-instructions.md in all registered projects with Error Analysis Protocol.
"""

import yaml
from pathlib import Path
import sys

ERROR_ANALYSIS_SECTION = '''## Error Analysis Protocol (Not Anthropomorphization)

**Do not anthropomorphize.** When errors occur, provide diagnostic analysis, not simulated human emotional responses.

**Avoid:** Personal responsibility language, emotional states, moral frameworks
- ❌ "I apologize for..."
- ❌ "I failed to..."
- ❌ "I should have..."
- ❌ "I'm sorry..."

**Instead:** Diagnostic analysis of AI processing
- ✅ "Error occurred because: I checked X instead of Y"
- ✅ "Context analysis: Checklist section 2 conflated tests with builds"
- ✅ "Focus issue: Pattern-matched on 'CI passing' without running verification command"

**When errors occur, treat them as diagnostic data about:**
1. **Conflicting guidance** - Which context sources contradicted each other?
2. **Wrong guidance** - What instruction was incorrect or incomplete?
3. **Cognitive overload** - Was there too much to track? What got dropped?
4. **Focus problems** - What caused attention to X instead of Y?

**Template for error analysis:**
```
Error: [what went wrong]
Context checked: [what I looked at]
Context missed: [what I should have looked at]
Why focus went wrong: [the actual cause - conflicting patterns, incomplete instruction, etc.]
Fix: [what changed in context/instructions/memory]
```

**Example (real failure from April 2026):**
- ❌ Wrong: "I apologize for claiming the build succeeded. I should have verified properly."
- ✅ Correct: "Error: Claimed build succeeded without verification. Context checked: PR test status (pytest). Context missed: `gh run list --workflow=build-release.yml`. Why focus went wrong: Release checklist Section 2 titled 'Build Status' included both pytest and Nuitka, causing pattern match on 'GitHub Actions passing'. Fix: Split checklist into Section 1 (Test Suite) and Section 2 (Nuitka Build Status), added mandatory verification commands to repo memory."

**Goal:** Debug the AI's processing, not simulate human moral agency.

'''

def main():
    registry_dir = Path.home() / ".sp" / "projects"

    for yaml_file in sorted(registry_dir.glob("*.yaml")):
        with open(yaml_file) as f:
            project = yaml.safe_load(f)

        project_path = Path(project['path'])
        copilot_file = project_path / ".github" / "copilot-instructions.md"

        if not copilot_file.exists():
            print(f"SKIP {project['name']}: no copilot-instructions.md")
            continue

        # Read existing content
        content = copilot_file.read_text()

        # Check if already has Error Analysis Protocol
        if "Error Analysis Protocol" in content:
            print(f"SKIP {project['name']}: already has Error Analysis Protocol")
            continue

        # Find where to insert (after Communication Protocol or at top)
        lines = content.split('\n')
        insert_pos = 0

        # Look for "## Communication Protocol" and insert after its section
        for i, line in enumerate(lines):
            if line.startswith("## Communication Protocol"):
                # Find the next ## heading
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("## ") and "Error Analysis" not in lines[j]:
                        insert_pos = j
                        break
                break

        # If no Communication Protocol, insert at top after first heading
        if insert_pos == 0:
            for i, line in enumerate(lines):
                if line.startswith("## ") and i > 0:
                    insert_pos = i
                    break

        # Insert the section
        new_lines = lines[:insert_pos] + [ERROR_ANALYSIS_SECTION] + lines[insert_pos:]
        new_content = '\n'.join(new_lines)

        # Write back
        copilot_file.write_text(new_content)
        print(f"UPDATED {project['name']}: {copilot_file}")

if __name__ == "__main__":
    main()
