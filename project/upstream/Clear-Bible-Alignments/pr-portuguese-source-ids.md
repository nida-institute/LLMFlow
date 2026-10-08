Fixes #15.

`data/por/alignments/JFA11/SBLGNT-JFA11-transfer.json` writes Macula source ids without the
`n` prefix that every other alignment file in the repository uses:

    BSB   (manual)     n40001001001   12 chars
    RV09  (manual)     n40001001001   12 chars
    JFA11 (transfer)    40001001001   11 chars

    source ids joining data/sources/SBLGNT.tsv
      before : 0 of 99,258
      after  : 99,258 of 99,258

The failure was silent rather than loud. Nothing errors: a consumer resolving these ids
against the SBLGNT source matches none of them and receives an empty result, which is
indistinguishable from a passage that genuinely has no alignments.

**What changed.** The `source` field only, one `n` per record, so the file grows by exactly
99,258 bytes. `documents`, `roles`, `meta` and the record structure are unchanged. Target ids
are untouched — they already join `data/por/targets/JFA11/nt_JFA11.tsv` at 100%.

The diff is large — 99,258 lines — because every record carries a source id.

JFA11 is the only `-transfer` file in this repository, so whether the same convention differs
for transferred alignments generally is worth a look.
