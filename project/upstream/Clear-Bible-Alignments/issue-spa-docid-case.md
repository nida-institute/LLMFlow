`data/spa/alignments/RV09/WLCM-RV09-manual.json` declares its source document as `wlcm`.
Every other file in the repository — and this file's own TOML sidecar — writes `WLCM`.
Observed on `main` at c99bd0a.

    $ jq -c '[.documents[].docid]' data/spa/alignments/RV09/WLCM-RV09-manual.json
    ["wlcm","RV09"]

    $ jq -c '[.documents[].docid]' data/fra/alignments/LSG/WLCM-LSG-manual.json
    ["WLCM","LSG"]

    $ grep -A2 '\[source\]' data/spa/alignments/RV09/WLCM-RV09-manual.toml
    identifier = "WLCM"

Checked across all 21 alignment files under `data/*/alignments/`: this is the only lowercase
docid among them.

**Effect.** A consumer comparing docids exactly — which validating a requested pair against
`documents` requires — does not match this file for a `WLCM` source request, so a pair that
exists appears unsupported. The failure is silent: nothing errors, the pair is simply absent.

**Suggested fix:** `"docid": "wlcm"` → `"docid": "WLCM"`.
