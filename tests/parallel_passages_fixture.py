"""Build a parallel-passages dataset from fixture XML with the real generator.

The tests state their own small database rather than reading the shipped one, so a UBS release
does not turn a correct engine red. Converting the fixture with `tools/parallel-passages/generate.py`
means the tests exercise the same conversion the shipped dataset came from.
"""

import importlib.util
from pathlib import Path

GENERATOR = Path(__file__).resolve().parent.parent / "tools" / "parallel-passages" / "generate.py"


def build_dataset(tmp_path: Path, xml: str) -> Path:
    """Write *xml*, convert it, and return the path of the dataset."""
    spec = importlib.util.spec_from_file_location("parallel_passages_generate", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    source = tmp_path / "ParallelPassages.xml"
    source.write_text(xml, encoding="utf-8")
    dataset = tmp_path / "parallel-passages.json"
    module.write(module.convert(source), dataset)
    return dataset
