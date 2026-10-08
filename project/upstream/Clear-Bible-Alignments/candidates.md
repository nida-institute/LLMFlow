---
Repository: Clear-Bible/Alignments  (public — https://github.com/Clear-Bible/Alignments)
Status: CANDIDATES — measured, not drafted as issues, nothing filed.
Caution: some sibling data (alignments-eng and other per-language repos) is
         copyright-restricted. Nothing from those repositories appears here, and
         nothing from them may go into a public issue.
---

# Clear-Bible/Alignments — candidate issues

Measured 2026-09-11 across the 21 tracked alignment files and their TOML sidecars.
`data/eng/alignments/BSB/foo.json` is untracked and is **not** a repository defect.

## Repository mechanics

### 1. A plain clone gets an LFS pointer instead of the corpus index

`data/catalog.tsv` is committed as a Git LFS pointer:

```
version https://git-lfs.github.com/spec/v1
oid sha256:485e4e54837fb7bd0b922b499bd81b3da6ea15c3ebaf7952ce120dd2085d20ee
size 3026
```

There is **no `.gitattributes` anywhere in the repository**, so nothing routes the file through
the LFS filter on checkout. The catalogue is the index to the whole corpus, and a normal clone
receives three lines of metadata in its place. Only this one file is affected; the alignment
JSONs are stored normally.

### 2. The catalogue does not index the published corpus

`data/catalog.tsv` lists 19 alignments keyed `lang+version+alignment`. Matching those keys
against the 21 published alignment files, **one** matches (`eng+YLT+WLC-YLT-manual`). Every other
catalogue row names an NA27 or WLC source, while the published files are SBLGNT, WLCM and BGNT.
(Key-format matching is an inference; the mismatch itself is not.)

## Metadata integrity

### 3. Four TOML sidecars will not parse

`tomllib` rejects them with "Cannot overwrite a value" — a duplicated key:

| file | error |
|---|---|
| `arb/alignments/AVD/SBLGNT-AVD-manual.toml` | line 32, column 105 |
| `arb/alignments/AVD/WLCM-AVD-manual.toml` | line 31, column 105 |
| `arb/alignments/ONAV/SBLGNT-ONAV-manual.toml` | line 30, column 62 |
| `eng/alignments/BSB/BGNT-BSB-manual.toml` | line 5, column 22 |

Their provenance is unreadable by any standard TOML parser.

### 4. The TOML and the JSON disagree about who made the alignment

`[alignment] team` in the TOML against `meta.creator` in the JSON, for the 17 readable pairs:
**15 disagree, 2 agree.** A selection:

| file | TOML `team` | JSON `creator` |
|---|---|---|
| `eng/BSB/SBLGNT-BSB-manual` | Biblica | BiblioNexus |
| `eng/BSB/WLCM-BSB-manual` | Clear | BiblioNexus |
| `eng/YLT/SBLGNT-YLT-manual` | Clear | GrapeCity |
| `spa/RV09/*` | BiblioNexus | United Bible Societies |
| `hau/OHCB/*` | BiblioNexus | United Bible Societies |
| `asm`, `ben`, `hin`, `fra/LSG/WLCM` | NLCI | Biblica |
| `rus/RUSSYN/*` | BiblioNexus | BiblioNexus.org |

`eng/YLT/SBLGNT-YLT-manual` names **three** parties for one alignment: `alignment.copyright`
Biblica, `team` Clear, `creator` GrapeCity.

Under CC BY, attribution is a licence term rather than metadata hygiene, so this is a licence
question and not a tidiness one.

### 5. `alignment.copyright` is present on only 8 of 17 readable sidecars

Absent on both `eng/BSB` files, and on `eng/YLT/WLC-YLT-manual` while its sibling in the same
directory has it.

### 6. The format version is recorded twice and spelled three ways

`meta.conformsTo = "0.3"` in the JSON, against `[alignment] format` in the TOML holding
`"Scripture Burrito 0.3"`, `"Scripture Burrito v0.3"`, or `"grapecity"`.

## Data defects

### 7. `WLCM-OHCB-manual.json` appears to carry the wrong corpus

It declares its source `docid` as **SBLGNT**, and its source selectors are Greek-shaped
(`n` + 11 digits). The filename says WLCM. Its shape is identical to `SBLGNT-OHCB-manual.json`
in the same directory. Not confirmed as a byte-for-byte duplicate.

### 8. Greek source identifiers are not uniform

13 files carry the `n` testament prefix; `SBLGNT-ONAV-manual` and `SBLGNT-JFA11-transfer` use
bare digits.

### 9. `BGNT-BSB` targets are 12 digits where every other BSB target is 11

Same target text, two tokenisations.

### 10. `WLCM-RV09-manual.json` declares `docid: "wlcm"`

Lowercase, against `WLCM` everywhere else.

## Scheme declarations

### 11. Declared schemes do not match the selectors they describe

Every source in all 21 files is declared `BCVWP`, including the 15 Greek sources that have **no
part digit**. Identical 11-digit targets are declared `BCVWP` in 12 files and `BCVW` in 7.

**This one has a known cause and a fix in flight upstream:** `biblealignlib`'s
`AlignmentGroup.py:49-58` sets the scheme from whether the docid is a recognised source, never
by inspecting the selectors. Fixing it there and regenerating is the right order — patching the
data first would be undone by the next write.
