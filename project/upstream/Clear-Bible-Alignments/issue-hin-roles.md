`data/hin/alignments/IRVHin/WLCM-IRVHin-manual.json` has no `roles` key. Every other
alignment file in the repository carries one. Observed on `main` at c99bd0a.

    $ jq -c '{documents: [.documents[].docid], roles: (.roles // null)}' \
        data/hin/alignments/IRVHin/WLCM-IRVHin-manual.json
    {"documents":["WLCM","IRVHin"],"roles":null}

    $ jq -c '{documents: [.documents[].docid], roles: (.roles // null)}' \
        data/hin/alignments/IRVHin/SBLGNT-IRVHin-manual.json
    {"documents":["SBLGNT","IRVHin"],"roles":["source","target"]}

`roles` is positional against `documents`, so it is the only thing inside the file that says
which of the two documents is the source. With it absent, that fact is available only from the
filename — and issue #12 is a file whose filename is wrong.

**Effect.** A consumer validating a requested pair against the file's own declaration cannot
confirm this pair. It must either reject a valid file or fall back to trusting the filename,
which #12 shows is not safe.

The TOML sidecar agrees with the `documents` order — `[source] identifier = "WLCM"`,
`[target] identifier = "IRVHin"` — so the intended value is not in doubt.

**Suggested fix:** add `"roles": ["source", "target"]`, in the position the other files use
(after `meta`, before `type`).
