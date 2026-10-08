Two alignment files misdeclare their own `documents`, and a consumer that validates a
requested pair against the file's own declaration — rather than against the filename, which
#12 shows can be wrong — rejects both as written.

**`data/hin/alignments/IRVHin/WLCM-IRVHin-manual.json` declares no `roles`.**

    "meta": {"conformsTo": "0.3", "creator": "Biblica"}, "type": "translation", ...

`roles` is positional against `documents`, so with it absent nothing inside the file says
which of its two documents is the source. Added `["source", "target"]`, matching the order of
its own `documents` block (`WLCM`, `IRVHin`), its TOML sidecar (`[source] identifier = "WLCM"`),
and the position the other twenty alignment files place it in.

**`data/spa/alignments/RV09/WLCM-RV09-manual.json` declares its source docid as `wlcm`.**

    {"docid": "wlcm", "scheme": "BCVWP"}

Every other file in the repository uses `WLCM`, as does this file's own TOML sidecar. Corrected
the case. A consumer comparing docids exactly — which the whole point of validating against
`documents` requires — cannot match this one.

**Scope.** Header only. Records are byte-unchanged: 257,930 and 257,188 respectively. The Hindi
file grows by 31 bytes; the Spanish by none. Both files still parse, and both now validate
against a `WLCM` source request.

Found while surveying all 21 alignment files by their declared `documents` and `roles` rather
than by filename.
