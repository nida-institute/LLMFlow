"""`data/parallel-passages.json` is current with its generator and its source.

The dataset is generated once from the UBS XML by `tools/parallel-passages/generate.py` and
committed. Regenerating it must reproduce the committed file byte for byte, so an edit to either
the generator or the file shows up here rather than in a consumer's output.
"""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "data" / "parallel-passages.json"
GENERATOR = ROOT / "tools" / "parallel-passages" / "generate.py"
SOURCE = Path.home() / "github/ubsicap/ubs-open-license/parallel passages/ParallelPassages.xml"

source_present = pytest.mark.skipif(not SOURCE.is_file(), reason="the UBS clone is not on this machine")


def generator():
    spec = importlib.util.spec_from_file_location("parallel_passages_generate", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@source_present
def test_the_dataset_is_current_with_its_generator(tmp_path):
    module = generator()
    regenerated = tmp_path / "parallel-passages.json"
    module.write(module.convert(SOURCE), regenerated)

    assert regenerated.read_bytes() == DATASET.read_bytes(), (
        "data/parallel-passages.json differs from what tools/parallel-passages/generate.py "
        "produces; regenerate it rather than editing it"
    )


def test_the_dataset_declares_what_it_holds():
    document = json.loads(DATASET.read_text(encoding="utf-8"))
    about = document["about"]

    assert about["groups"] == len(document["groups"])
    assert about["members"] == sum(len(group["members"]) for group in document["groups"])
    assert about["match"] == ["no_match", "partial", "full"]
    assert about["counted_in"] == ["BHS", "Rahlfs", "UBSGNT5"]


def test_every_member_has_both_blocks_and_values_from_the_declared_sets():
    document = json.loads(DATASET.read_text(encoding="utf-8"))
    match = set(document["about"]["match"])
    counted_in = set(document["about"]["counted_in"])

    for group in document["groups"]:
        assert group["editions"] == sorted({m["counted"]["text"] for m in group["members"]})
        for member in group["members"]:
            assert member["addressed"]["versification"] == "org"
            assert member["addressed"]["verses"], member["addressed"]["reference"]
            assert member["counted"]["text"] in counted_in
            assert member["match"] and set(member["match"]) <= match
