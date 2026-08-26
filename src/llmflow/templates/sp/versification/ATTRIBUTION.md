# Versification mappings — source and licence

The `*.json` files in this directory are **unmodified copies** from the Copenhagen Alliance
versification specification.

| | |
|---|---|
| Source | <https://github.com/Copenhagen-Alliance/versification-specification> |
| Path in that repository | `versification-mappings/standard-mappings/` |
| Commit | `5f3f82f3dc3cfd25fffc6ff04f3630763972258c` (`master`, 2025-08-04) |
| Licence | Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) |
| Licence text | <https://creativecommons.org/licenses/by-sa/4.0/> |

Six schemes are included: `org` (the original-language hub), `eng`, `lxx`, `vul`, `rsc` and
`rso`. The upstream directory also holds `ethiopian_custom.json`, a named custom mapping rather
than a standard scheme; it is not copied here, and a custom mapping is supplied by placing it in
this directory.

## Modifying these files

**Do not edit them here.** An edit is an adaptation under CC BY-SA 4.0, which obliges you to
license the result under the same terms and to state what you changed. `sp doctor` also treats
these files as generated and restores them, so a local edit would not survive.

Report a defect upstream instead. Seven entries are skipped on load, each named in a warning:

| scheme | entry | |
|---|---|---|
| `vul` | `DAG 3:52-23` → `S3Y 1:30-31` | a descending range; the two-verse target suggests `DAG 3:52-53` |
| `vul` | `DAG 13:1-63` → `SUS 1:63` | 63 verses to 1 |
| `vul` | `DAG 14:1-42` → `BEL 1:42` | 42 verses to 1 |
| `rsc` | `PSA 89:0-1` → `PSA 90:0` | 2 verses to 1 |
| `rsc` | `PSA 141:0` → `PSA 142:0-1` | 1 verse to 2 |
| `rso` | `PSA 86:0-1` → `PSA 87:1` | 2 verses to 1 |
| `rso` | `PSA 89:2-6` → `PSA 90:1-6` | 5 verses to 6 |

The specification's own JSON schema permits unequal ranges, so these may be intended rather than
mistaken — several look like merges, which the specification expresses with `mergedVerses`
instead. `llmflow.utils.versification` skips such an entry and says so rather than guessing where
a reference lands.

## What this engine reads

`maxVerses`, `mappedVerses`, `excludedVerses` and `basedOn`. The specification also defines
`mergedVerses` and `partialVerses`, which are **not yet interpreted** — loading a scheme that
carries either warns and names the count. `lxx.json` carries 74 `partialVerses` entries.
