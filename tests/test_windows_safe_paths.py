"""Paths a pipeline makes can be checked out, and read, on Windows.

Two failures seen with semdom-greek-lexicon's pipelines/semlex.yaml:

- `group_by_prefix: 2` filed `ὁ.audit.md` (stem `ὁ.audit`) under a folder named `ο.`. Windows
  refuses a name ending in a period, so the repository the pipeline wrote into could not be cloned
  there. The prefix now ends where the name does.
- On Windows, Saxon could not turn the relative stylesheet path `xslt\\x.xslt` into a URI, and
  the `xslt` step failed with "Invalid URI file:///C:/...". It is given an absolute path.
"""
from __future__ import annotations

import pytest

from llmflow.cli import main


def _run(tmp_path, monkeypatch, steps: str) -> None:
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text("name: p\nsteps:\n" + steps, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    main(["run", "--pipeline", str(pipeline)])


class TestGroupByPrefix:
    def test_a_one_letter_name_with_a_further_extension_is_filed_under_the_letter(self, tmp_path, monkeypatch):
        _run(tmp_path, monkeypatch,
             "  - name: audit\n"
             "    type: json\n"
             "    value: audit\n"
             "    output: audit\n"
             "    saveas:\n"
             "      path: out/ὁ.audit.md\n"
             "      group_by_prefix: 2\n")

        assert (tmp_path / "out" / "ο" / "ὁ.audit.md").read_text(encoding="utf-8").strip() == "audit"
        assert [d.name for d in (tmp_path / "out").iterdir()] == ["ο"]

    def test_a_two_letter_name_is_filed_as_before(self, tmp_path, monkeypatch):
        _run(tmp_path, monkeypatch,
             "  - name: entry\n"
             "    type: json\n"
             "    value: entry\n"
             "    output: entry\n"
             "    saveas:\n"
             "      path: out/σύ.entry.md\n"
             "      group_by_prefix: 2\n")

        assert (tmp_path / "out" / "συ" / "σύ.entry.md").exists()


class TestXslt:
    def test_a_relative_stylesheet_path_is_found(self, tmp_path, monkeypatch):
        pytest.importorskip("saxonche")
        (tmp_path / "xslt").mkdir()
        (tmp_path / "xslt" / "upper.xslt").write_text(
            '<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">\n'
            '  <xsl:output method="text"/>\n'
            '  <xsl:template match="/">\n'
            '    <xsl:value-of select="upper-case(/word)"/>\n'
            "  </xsl:template>\n"
            "</xsl:stylesheet>\n",
            encoding="utf-8",
        )
        _run(tmp_path, monkeypatch,
             "  - name: upper\n"
             "    type: xslt\n"
             "    inputs:\n"
             "      stylesheet_path: xslt/upper.xslt\n"
             '      xml_string: "<word>logos</word>"\n'
             "    output: upper\n"
             "    saveas: out/upper.txt\n")

        assert (tmp_path / "out" / "upper.txt").read_text(encoding="utf-8").strip() == "LOGOS"
