"""The GUI must find a consumer's pipelines without knowing that consumer's folder name.

`server.py` guessed two locations: `<project>/pipelines` and `<project>/LLMFlow/pipelines`.
The second was a specific consumer's layout — `ears-to-hear/LLMFlow` — hardcoded into the
engine. That directory was renamed to `scriptorium` on 2026-07-14, leaving an untracked husk
with one file in it behind. Measured 2026-08-24: `scriptorium/` holds 4,814 files and is
tracked; `LLMFlow/` holds 1 and is not. So the GUI has been looking in the husk and finding
nothing, and would keep doing so for any consumer that chose a third name.

Naming consumer directories in the engine means the engine goes stale every time a consumer
renames a folder. Rule `one-design`: find the directory by shape, not by a list of names that
has to be maintained somewhere it cannot be seen.

The fact that corrected this was sitting in a deleted `~/.claude` memory file that no
repository could see — which is the argument for the transparent-space migration, not an
aside.
"""
from pathlib import Path

from llmflow.gui.server import find_pipelines_dir


def test_finds_pipelines_at_the_project_root(tmp_path):
    (tmp_path / "pipelines").mkdir()
    assert find_pipelines_dir(tmp_path) == tmp_path / "pipelines"


def test_finds_pipelines_one_level_down_whatever_the_folder_is_called(tmp_path):
    """The case that was broken: a consumer keeping the working tree in a subdirectory."""
    (tmp_path / "scriptorium" / "pipelines").mkdir(parents=True)
    assert find_pipelines_dir(tmp_path) == tmp_path / "scriptorium" / "pipelines"


def test_the_project_root_wins_over_a_subdirectory(tmp_path):
    (tmp_path / "pipelines").mkdir()
    (tmp_path / "scriptorium" / "pipelines").mkdir(parents=True)
    assert find_pipelines_dir(tmp_path) == tmp_path / "pipelines"


def test_returns_none_when_there_is_nothing_to_find(tmp_path):
    (tmp_path / "docs").mkdir()
    assert find_pipelines_dir(tmp_path) is None


def test_ignores_hidden_and_vendor_directories(tmp_path):
    """A `pipelines` dir inside .venv or node_modules is not the project's."""
    (tmp_path / ".venv" / "pipelines").mkdir(parents=True)
    (tmp_path / "node_modules" / "pipelines").mkdir(parents=True)
    assert find_pipelines_dir(tmp_path) is None


def test_a_missing_project_path_is_not_an_error(tmp_path):
    assert find_pipelines_dir(tmp_path / "does-not-exist") is None


def test_no_consumer_folder_name_is_hardcoded_in_the_server():
    """Guard: the engine must not name a specific consumer's directory layout again."""
    source = Path(__file__).resolve().parent.parent / "src" / "llmflow" / "gui" / "server.py"
    text = source.read_text(encoding="utf-8")
    for name in ("'LLMFlow'", '"LLMFlow"', "'scriptorium'", '"scriptorium"'):
        assert name not in text, (
            f"{name} is hardcoded in server.py. Consumer directory names belong to the "
            "consumer; find the directory by shape instead."
        )
