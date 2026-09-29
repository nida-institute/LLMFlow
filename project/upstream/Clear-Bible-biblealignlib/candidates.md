---
Repository: Clear-Bible/biblealignlib
Status: CANDIDATES — measured, not drafted as issues, nothing filed.
---

# biblealignlib — candidate issues

Found while making the library conform to alignment format 0.4. Each was measured on
`main` at `c99bd0a`-era clone (2026-09-11). None is caused by our changes.

## 1. A fresh clone cannot install

`poetry install` fails outright:

> pyproject.toml changed significantly since poetry.lock was last generated.

`pyproject.toml` last changed at `3977334` ("v 0.4.0", 2026-05-08); `poetry.lock` has not been
regenerated since 2026-03-17. Anyone cloning the repository is blocked at the first step.

**Fix:** regenerate and commit `poetry.lock`. One command, no code change.

## 2. The library points at a repository layout the published data no longer uses

Roughly 30 sites reference `CLEARROOT / "alignments-{lang}/data"`, while the published data
sits at `Alignments/data/{lang}`. Most are docstrings, but several are **live defaults**:

- `interlinear/reverse.py:20`
- `util/MergeAlignments.py:22`
- `util/merger.py:19,24`
- `autoalign/mapper.py:13`, `reader.py:56`, `scorer.py:272`, `writer.py:49`
- `autoalign/runeflomal.py:22`, `eflomal.py:12`

`AGENTS.md` carries **both** layouts, and one fixture example already uses the newer
`CLEARROOT / "Alignments/data/eng"` — so the migration was started and left unfinished.

## 3. The test suite cannot run without private repositories

Four test modules hardcode `ENGLANGDATAPATH = CLEARROOT / "alignments-eng/data"`, and
`TestAlignmentSetHin` additionally needs `alignments-hin`. Neither repository is reachable to a
public clone. On a machine with `alignments-eng` but not `alignments-hin`:

```
370 passed, 3 errors
```

all three errors being `TestAlignmentSetHin` path assertions.

Some of this data is copyright-restricted and cannot simply be made public. But a contributor
without it currently cannot get a green run at all, and cannot tell which failures are theirs.
**Worth considering:** synthetic fixtures for the tests that only need structure, so the
suite is green without restricted data and the data-dependent tests skip rather than error.

## 4. `test_AlignmentGroup.py` is not Black-clean on `main`

`black --check` reformats four `TestTopLevelGroups` tests (around lines 494, 524, 539) —
generator expressions split across lines in a way Black rejects. Pre-existing and unrelated to
any current work; left untouched deliberately so it does not ride along in an unrelated PR.

## 5. `mypy` is configured to check a directory that does not exist

`pyproject.toml`:

```toml
[tool.mypy]
files = ["src"]
```

There is no `src/` directory — `packages = [{include = "biblealignlib"}]`. So a bare `mypy` run
checks nothing, and `disallow_untyped_defs = "True"` is not actually enforced anywhere.

## 6. The library and the published specification disagree about which spec is current

`AlignmentGroup.py`'s module docstring and `AGENTS.md` both cite:

> Scripture Burrito Alignment Standard, v 0.3,
> https://docs.google.com/document/d/1zR5gsrm3gIoNiHVBlWz5_BBw3N-Ew1-4M5rMsFrPzSw/

while the specification at https://github.com/bible-technology/alignment-spec is at **0.4**, and
the Scripture Burrito flavor page points there for the format. 0.4 removed the group-less
top-level form (commit `e563857b`, "don't skip singletone groups") that the library still writes.

This is arguably the largest interoperability problem found: two specifications, different
contents, and the implementation follows the one that is not linked from the flavor page.

## 7. Record ids are renumbered on a different width than published data uses

**Not a spec matter** — `meta.id` is the library's own identifier scheme, and a library may
define its own so long as it documents it. The practical point is narrower:

- published files carry `"id": "40001001.001"` — three digits
- `_record_dict` writes `f"{bcv}.{bcv_counters[bcv]:02}"` — two digits

So regenerating the published corpus renumbers every record id in all 21 files: one-time diff
noise across the whole repository, on a change that is otherwise structural. Their own reader
test asserts the three-digit form (`alrec["41004003.001"]`), which passes only because it reads
published data rather than round-tripping.

Worth settling *before* any regeneration, and worth documenting the scheme wherever it lands.

## 8. No burrito container is ever written

No `metadata.json`, no `flavorType`, no ingredients anywhere in the package. `AlignmentSet`
computes `tomlpath` and `check_files()` asserts it exists — but **nothing ever opens it**; there
is no `tomllib` import in the package. So the copyright, licence and team recorded in the TOML
sidecar are carried by no code, and the alignment files are not packaged as burritos at all.

This is the subject of planned work (W3/W4), recorded here so the gap is on the record.
