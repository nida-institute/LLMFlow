"""A write path containing an unresolved `${var}` must raise, not become a directory.

Reported by Ears to Hear, 2026-08-17
(`scriptorium/collab/sp/2026-08-17-unresolved-variable-becomes-a-directory.md`).

`resolve()` returns an unresolvable `${var}` as its own literal text, and every write
helper in `utils/io.py` fed that text straight to `Path(...).mkdir(parents=True,
exist_ok=True)`. The filesystem obliges. So a run whose variable did not resolve did not
fail — it created a directory literally named `${intermediate_file_directory}` and wrote
real output into it. Nothing raised, nothing warned, the run reported success.

The reporter found **209 files, 3.7 MB** in three such directories. They had been there six
weeks and were committed to git without anyone noticing. Ruth and Philemon intermediates
were written where nothing reads them while every downstream step read the real directory
and found whatever was there from before.

The failure is silent in three compounding ways: the run succeeds, the output *looks* like
output (well-formed JSON of the right size, sitting beside the real tree), and
`exist_ok=True` means a second run appends to the wrong tree rather than colliding — so age
never makes it more visible.

**The guard already existed, twice, on the two paths that do not write:**

| Path | saveas checked for `${` |
|---|---|
| `sp lint` | yes — `linter.py:844`, `:850`, via `_ensure_path_resolved_for_lint` at `:874` |
| rewind | yes — `rewind.py:137`, `:144`, via `_ensure_path_resolved` at `:169` |
| a normal run | **no** — this is what these tests pin |

Both guards have been in the tree since `900c9a2` (2026-03-16). The two guarded paths agree
with each other, which is exactly why nothing looked wrong.

These tests guard the **write helpers** rather than `saveas` resolution, because the
reporter's second question was whether `saveas` is the only way a path reaches `mkdir`. It
is not: `save_markdown_as` and `save_xml` take `output_dir` directly, and function/plugin
steps can pass paths that never went through saveas at all. A saveas-only guard would leave
those uncovered.

`save_json` is included even though the report did not name it — it has the same
`mkdir(parents=True, exist_ok=True)` shape at `utils/io.py:373`.
"""

from pathlib import Path

import pytest

from llmflow.utils import io as io_utils

UNRESOLVED = "${intermediate_file_directory}/build-book/out.json"
UNRESOLVED_DIR = "${output_file_directory}/book-summaries"


def _tree_is_empty(root: Path) -> bool:
    return not any(root.iterdir())


# --- the four write helpers must refuse ------------------------------------------


def test_save_text_refuses_an_unresolved_path(tmp_path: Path):
    """The exact reproduction from the report."""
    target = tmp_path / UNRESOLVED

    with pytest.raises(ValueError) as excinfo:
        io_utils.save_text("payload", str(target))

    assert "${" in str(excinfo.value), "the error must quote the offending path"
    assert _tree_is_empty(tmp_path), "a refused write still created directories"


def test_save_json_refuses_an_unresolved_path(tmp_path: Path):
    """Not named in the report, but the same shape at utils/io.py:373."""
    target = tmp_path / UNRESOLVED

    with pytest.raises(ValueError):
        io_utils.save_json({"a": 1}, str(target))

    assert _tree_is_empty(tmp_path)


def test_save_markdown_as_refuses_an_unresolved_output_dir(tmp_path: Path):
    """`output_dir` is passed directly — it never went through saveas resolution."""
    with pytest.raises(ValueError):
        io_utils.save_markdown_as("text", "MRK 1", output_dir=str(tmp_path / UNRESOLVED_DIR))

    assert _tree_is_empty(tmp_path)


def test_save_xml_refuses_an_unresolved_output_dir(tmp_path: Path):
    with pytest.raises(ValueError):
        io_utils.save_xml("<a/>", "entry", output_dir=str(tmp_path / UNRESOLVED_DIR))

    assert _tree_is_empty(tmp_path)


# --- it must not become a directory ----------------------------------------------


def test_no_stray_directory_is_created(tmp_path: Path):
    """The specific harm: `${intermediate_file_directory}/` appearing on disk.

    `exist_ok=True` means a second run appends to the wrong tree rather than colliding,
    so this must fail closed on the first attempt.
    """
    target = tmp_path / UNRESOLVED

    with pytest.raises(ValueError):
        io_utils.save_text("payload", str(target))

    stray = tmp_path / "${intermediate_file_directory}"
    assert not stray.exists(), "the literal variable name was created as a directory"


def test_a_curly_only_placeholder_is_refused_too(tmp_path: Path):
    """The two existing guards test `"${" in path or "{" in path` — match them.

    The report records artifacts from a `{curly}`-vs-`${dollar}` matcher collision:
    directories named `$${output_file_directory}` and files named
    `$08-$RUT-book-summary.json`. A path carrying either spelling is not resolved.
    """
    with pytest.raises(ValueError):
        io_utils.save_text("payload", str(tmp_path / "{book_code}" / "out.md"))

    assert _tree_is_empty(tmp_path)


# --- and must not get in the way of real paths -----------------------------------


def test_a_resolved_path_still_writes(tmp_path: Path):
    target = tmp_path / "outputs" / "intermediate" / "out.json"

    result = io_utils.save_text("payload", str(target))

    assert Path(result).read_text(encoding="utf-8") == "payload"


def test_a_resolved_output_dir_still_writes(tmp_path: Path):
    out = tmp_path / "outputs" / "md"

    result = io_utils.save_markdown_as("hello", "MRK 1", output_dir=str(out))

    assert Path(result).exists()


def test_a_dollar_without_braces_is_allowed(tmp_path: Path):
    """`$` alone is a legal filename character; only a placeholder is a problem."""
    target = tmp_path / "prices" / "cost$100.md"

    result = io_utils.save_text("payload", str(target))

    assert Path(result).exists()
