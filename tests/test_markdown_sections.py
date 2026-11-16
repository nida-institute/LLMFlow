"""`merge_sections` places a model's additions under a document's headings, and
`reference_coverage` reports which references a text holds. Both run without a model.

Seen in semdom-greek-lexicon's SemLex pipeline: asked to add definitions to an entry of 37
references and return it whole, a model kept 14; asked to audit the result, it reported 35.
"""
from __future__ import annotations

import json

import yaml

from llmflow.cli import main

ENTRY = """# λέγω

## I. To say

**References:**
- **Mark 3:21**: ἔλεγον γὰρ ὅτι Ἐξέστη
- **John 1:29**: λέγει· Ἴδε ὁ ἀμνὸς

### I.1 Indirect speech

**References:**
- **John 6:14**: ἔλεγον ὅτι Οὗτός ἐστιν

```
## not a heading, inside a fence
```

## II. To call

**References:**
- **Matthew 9:9**: Μαθθαῖον λεγόμενον
"""


def _run(tmp_path, monkeypatch, steps: list) -> None:
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(yaml.safe_dump({"name": "p", "steps": steps}, allow_unicode=True), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    main(["run", "--pipeline", str(pipeline)])


def _merge(tmp_path, monkeypatch, additions) -> str:
    _run(tmp_path, monkeypatch, [
        {"name": "entry", "type": "json", "value": ENTRY, "output": "entry"},
        {"name": "additions", "type": "json", "value": additions, "output": "additions"},
        {"name": "merge", "type": "function", "function": "llmflow.utils.markdown_sections.merge_sections",
         "inputs": {"markdown": "${entry}", "additions": "${additions}"}, "output": "merged",
         "saveas": "out/merged.md"},
    ])
    return (tmp_path / "out" / "merged.md").read_text(encoding="utf-8")


class TestMergeSections:
    def test_each_addition_goes_under_its_heading_and_nothing_is_lost(self, tmp_path, monkeypatch):
        merged = _merge(tmp_path, monkeypatch, {
            "intro": "**Core Meaning:** To say.",
            "sections": [
                {"heading": "I", "before": "Speech, direct or reported.", "after": "> Note: very common."},
                {"heading": "I.1", "before": "Reported speech.", "after": ""},
                {"heading": "II.", "before": "Naming.", "after": "**Synonyms:** καλέω (call)"},
            ],
            "end": "## Morphology\n\n| λέγω |",
        })

        for line in ENTRY.splitlines():
            assert line in merged.splitlines()
        assert merged.index("# λέγω") < merged.index("**Core Meaning:**") < merged.index("## I. To say")
        assert merged.index("## I. To say") < merged.index("Speech, direct") < merged.index("- **Mark 3:21**")
        assert merged.index("- **John 1:29**") < merged.index("> Note: very common.") < merged.index("### I.1")
        assert merged.index("### I.1") < merged.index("Reported speech.") < merged.index("- **John 6:14**")
        assert merged.index("## II. To call") < merged.index("Naming.") < merged.index("- **Matthew 9:9**")
        assert merged.rstrip().endswith("| λέγω |")

    def test_a_heading_inside_a_fence_is_text(self, tmp_path, monkeypatch):
        # The fenced line "## not a heading" would have the label "not".
        merged = _merge(tmp_path, monkeypatch, {"sections": [{"heading": "not", "before": "x", "after": ""}]})
        assert merged.index("## Not placed") < merged.index("**not**")

    def test_an_addition_for_a_heading_the_document_lacks_is_kept_and_named(self, tmp_path, monkeypatch):
        merged = _merge(tmp_path, monkeypatch, {"sections": [{"heading": "III", "before": "To mean.", "after": ""}]})
        assert merged.index("## Not placed") < merged.index("**III**") < merged.index("To mean.")

    def test_additions_may_arrive_as_a_json_string(self, tmp_path, monkeypatch):
        merged = _merge(tmp_path, monkeypatch, json.dumps({"intro": "Core."}))
        assert merged.index("# λέγω") < merged.index("Core.") < merged.index("## I. To say")


class TestReferenceCoverage:
    def _audit(self, tmp_path, monkeypatch, references) -> str:
        _run(tmp_path, monkeypatch, [
            {"name": "text", "type": "json", "value": ENTRY, "output": "text"},
            {"name": "refs", "type": "json", "value": references, "output": "refs"},
            {"name": "audit", "type": "function", "function": "llmflow.utils.reference_coverage.reference_coverage",
             "inputs": {"references": "${refs}", "text": "${text}"}, "output": "audit",
             "saveas": "out/audit.md"},
        ])
        return (tmp_path / "out" / "audit.md").read_text(encoding="utf-8")

    def test_the_missing_references_are_named(self, tmp_path, monkeypatch):
        audit = self._audit(tmp_path, monkeypatch, {"references": [
            {"reference": "Mark 3:21"}, {"reference": "Mark 3:2"}, {"reference": "Luke 1:24"},
            {"reference": "John 6:14"},
        ]})
        assert "- **References analysed:** 4" in audit
        assert "- **In the text:** 2" in audit
        assert "- **Status:** FAIL" in audit
        assert audit.split("## Missing")[1].split() == ["-", "Mark", "3:2", "-", "Luke", "1:24"]

    def test_all_present_is_a_pass(self, tmp_path, monkeypatch):
        audit = self._audit(tmp_path, monkeypatch, ["John 1:29", "Matthew 9:9"])
        assert "- **Status:** PASS" in audit and "## Missing" not in audit
