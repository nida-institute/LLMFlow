"""A `json` step saves and appends its value the way every other step does.

`saveas` and `append_to` are common keys, and lint accepts both on a `json` step. Until this was
fixed the handler stored the value and returned, so a `saveas` wrote nothing and an `append_to`
collected nothing — silently, with the list still at its declared default.
"""

import json

from llmflow import load_pipeline


def run(tmp_path, steps, variables=""):
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(
        "name: json-outputs\n" + variables + "steps:\n" + steps,
        encoding="utf-8",
    )
    return load_pipeline(pipeline).run()


def test_saveas_writes_the_value(tmp_path):
    out = tmp_path / "value.json"
    run(
        tmp_path,
        "  - name: build\n"
        "    type: json\n"
        "    value: {a: 1, b: [2, 3]}\n"
        "    output: built\n"
        f"    saveas: {out}\n",
    )

    assert json.loads(out.read_text(encoding="utf-8")) == {"a": 1, "b": [2, 3]}


def test_append_to_collects_one_value_per_iteration(tmp_path):
    out = tmp_path / "collected.json"
    run(
        tmp_path,
        "  - name: each\n"
        "    type: for-each\n"
        "    for: item\n"
        '    in: "${items}"\n'
        "    steps:\n"
        "      - name: wrap\n"
        "        type: json\n"
        "        value:\n"
        '          name: "${item}"\n'
        "        output: wrapped\n"
        "        append_to: collected\n"
        "  - name: save\n"
        "    type: save\n"
        '    content: "${collected}"\n'
        f"    path: {out}\n",
        variables="variables:\n  items: [alpha, beta]\n  collected: []\n",
    )

    assert json.loads(out.read_text(encoding="utf-8")) == [{"name": "alpha"}, {"name": "beta"}]
