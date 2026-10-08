"""Generate a worked-example file for the alignment operation (R1 + R5).

Throwaway. Regenerate with:
    hatch run python tmp/gen_alignment_demo.py > tmp/alignment-worked-examples.md
"""
import json, collections, sys, bisect

BASE = "/Users/jonathan/github/Clear/Alignments/data"


def load_source(name):
    rows = {}
    with open(f"{BASE}/sources/{name}.tsv") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            c = (line.rstrip("\n").split("\t") + [""] * len(hdr))[: len(hdr)]
            rows[c[0]] = dict(zip(hdr, c))
    return rows


def load_target(lang, ver, testament):
    rows, order = {}, []
    with open(f"{BASE}/{lang}/targets/{ver}/{testament}_{ver}.tsv") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            c = (line.rstrip("\n").split("\t") + [""] * len(hdr))[: len(hdr)]
            rows[c[0]] = dict(zip(hdr, c))
            order.append(c[0])
    return rows, order, hdr


def load_alignment(lang, ver, src):
    d = json.load(open(f"{BASE}/{lang}/alignments/{ver}/{src}-{ver}-manual.json"))
    s2t = collections.defaultdict(set)
    t2s = collections.defaultdict(set)
    s2rec = collections.defaultdict(set)
    aligned = set()
    for n, r in enumerate(d["records"]):
        for s in r["source"]:
            s2t[s].update(r["target"])
            s2rec[s].add(n)
            for t in r["target"]:
                t2s[t].add(s)
        aligned.update(r["target"])
    return d, s2t, t2s, s2rec, aligned


def join(tokens, trows):
    """Assemble target text in target order, honouring skip_space_after where present."""
    out = []
    for t in tokens:
        r = trows[t]
        out.append(r["text"])
        if not r.get("skip_space_after"):
            out.append(" ")
    return "".join(out).strip()


def join_marking_gaps(tokens, trows, torder):
    """Assemble target text, writing ` … ` where the tokens are not a contiguous run.

    R15 applies on the target side as well: a record whose English is scattered must not be closed
    up into text the translation never contains. Without this, Luke 1:3's discontinuous record
    renders as "Thereforehaving carefully investigated".
    """
    if not tokens:
        return ""
    pos = {t: i for i, t in enumerate(torder)}
    out, prev = [], None
    for t in tokens:
        if prev is not None and pos[t] != pos[prev] + 1:
            out.append(" … ")
        elif prev is not None and not trows[prev].get("skip_space_after"):
            out.append(" ")
        out.append(trows[t]["text"])
        prev = t
    return "".join(out).strip()


def alignment_units(span, records, s2rec, tset):
    """One entry per alignment record touching the span — the aligners' own units, not ours.

    A record is the alignment's claim about what corresponds to what, including when its source
    words are not adjacent (R14). An earlier version of this script derived its own "blocks" by a
    contiguity heuristic; that invented a unit where the data already had one, absorbed the words
    a discontinuous record skips, and asserted groupings the file does not. Removed 2026-09-14 at
    the Captain's direction.

    A source unit aligning to no record appears on its own, so it stays visible.
    """
    inspan, seen, units = set(span), set(), []
    for s in span:
        recs = sorted(s2rec.get(s, ()))
        if not recs:
            units.append({"src": [s], "tgt": []})
            continue
        for n in recs:
            if n in seen:
                continue
            seen.add(n)
            r = records[n]
            src = sorted(x for x in r["source"] if x in inspan)
            if src:
                units.append({"src": src, "tgt": sorted(t for t in r["target"] if t in tset)})
    return units


def word_index(sid):
    return int(sid.lstrip("no")[8:11])


def source_phrase(ids, srows):
    """Join source surface forms.

    Morphemes of one word (same id less the part digit) run together. R15: where the unit skips a
    word that belongs to something else, write the gap with a marker rather than closing it up.
    """
    out = []
    for i, s in enumerate(ids):
        txt = srows.get(s, {}).get("text", "?")
        if i == 0:
            out.append(txt)
            continue
        prev = ids[i - 1]
        if len(s) == 13 and s[:-1] == prev[:-1]:
            out.append(txt)                       # another morpheme of the same word
        elif word_index(s) > word_index(prev) + 1:
            out.append(" … " + txt)               # R15: a word belonging to something else was skipped
        else:
            out.append(" " + txt)
    return "".join(out)


def demo(title, lang, ver, src, testament, book, chap, v_from, v_to, note=""):
    d, s2t, t2s, s2rec, aligned = load_alignment(lang, ver, src)
    srows = load_source(src)
    trows, torder, thdr = load_target(lang, ver, testament)
    tset = set(torder)

    pfx = "n" if src.startswith(("SBLGNT", "BGNT")) else "o"
    def in_span(sid):
        if not sid.startswith(pfx):
            return False
        dg = sid[1:]
        return dg[:2] == book and dg[2:5] == f"{chap:03d}" and v_from <= int(dg[5:8]) <= v_to

    # Every source unit in the range, from the source text — not only the aligned ones, so a
    # source word aligning to nothing stays visible rather than vanishing from the table.
    span = sorted(s for s in srows if in_span(s))
    unaligned_src = [s for s in span if not (s2t.get(s, set()) & tset)]
    # R6: alignment is verse-scoped, so each verse the span draws from is settled on its own,
    # then concatenate in verse order. Equivalent to one stretch only when whole verses are covered.
    mine = {t for s in span for t in s2t.get(s, set())} & tset
    unaligned_inside, other_unit, result = [], [], []
    for v in sorted({s[1:][:8] for s in span}):
        vmine = {t for s in span if s[1:][:8] == v for t in s2t.get(s, set())} & tset
        if not vmine:
            continue
        lo_v, hi_v = min(vmine), max(vmine)
        # Verse-final punctuation sits after the verse's last aligned token, so bounds that
        # stops at hi_v yields "wordTherefore". Extend over trailing unaligned tokens in this
        # verse. This is the D2 choice being demonstrated, not a ruling.
        vall = [t for t in torder if t[:8] == v]
        i = vall.index(hi_v)
        while i + 1 < len(vall) and vall[i + 1] not in aligned:
            i += 1
        hi_v = vall[i]
        j = vall.index(lo_v)
        while j > 0 and vall[j - 1] not in aligned:
            j -= 1
        lo_v = vall[j]
        vwin = [t for t in vall if lo_v <= t <= hi_v]
        vabs = [t for t in vwin if t not in aligned]
        vfor = [t for t in vwin if t in aligned and t not in vmine]
        unaligned_inside += vabs
        other_unit += vfor
        result += sorted(vmine | set(vabs))
    lo, hi = min(mine), max(mine)
    covered = [t for t in torder if lo <= t <= hi]

    print(f"## {title}\n")
    if note:
        print(f"{note}\n")
    print(f"- **pair** `from: {src}` → `to: {ver}`, declared in the file as "
          f"`{d['documents'][0]['docid']}` ({d['documents'][0]['scheme']}) → "
          f"`{d['documents'][1]['docid']}` ({d['documents'][1]['scheme']})")
    print(f"- **source units in span**: {len(span)}   "
          f"(`{span[0]}` … `{span[-1]}`), of which "
          f"**{len(unaligned_src)} align to nothing**")
    print(f"- **target tokens aligned**: {len(mine)}   "
          f"**unaligned tokens inside the span**: {len(unaligned_inside)}   "
          f"**tokens belonging to a different source unit**: {len(other_unit)}")
    print(f"- **from `{lo}` to `{hi}`** — {len(covered)} target tokens in that range, "
          f"and the tokens are {'CONTIGUOUS in every verse' if not other_unit else 'NOT contiguous'}\n")

    print("### The English this produces (R1 + R5, target order)\n")
    print(f"> {join(result, trows)}\n")

    units = alignment_units(span, d["records"], s2rec, tset)
    rendered = []
    for n, u in enumerate(units, 1):
        ts = u["tgt"]
        disc = len(u["src"]) > 1 and (
            word_index(u["src"][-1]) - word_index(u["src"][0]) + 1 != len(u["src"]))
        rendered.append({
            "n": n,
            "src": source_phrase(u["src"], srows),
            "eng": join_marking_gaps(ts, trows, torder) if ts else "`nothing`",
            "key": ts[0] if ts else "",
            "disc": disc,
        })

    ndisc = sum(1 for r in rendered if r["disc"])
    print(f"### Constituent ↔ constituent — {len(units)} alignment records\n")
    print("Each entry is one **alignment record** — the aligners' own claim about what corresponds "
          "to what. These are the alignment's units, not units derived here. A source unit that no "
          "record covers appears on its own, so it stays visible.\n")
    if ndisc:
        print(f"**{ndisc} record{'s' if ndisc != 1 else ''} group source words that are not "
              f"adjacent** (R14). The gap is written ` … ` (R15): the words between belong to a "
              f"different record and appear as their own entries.\n")
    print("The two lists hold the same records; only their sequence differs, and that difference "
          "is the reordering.\n")

    print("**(1) Source order**\n")
    for r in rendered:
        flag = "  ← discontinuous" if r["disc"] else ""
        print(f"- `{r['n']}` **{r['src']}** ↔ {r['eng']}{flag}")
    print()

    print("**(2) Target order**\n")
    moved = 0
    prev = -1
    for r in sorted(rendered, key=lambda r: (r["key"] == "", r["key"])):
        flag = "  ← discontinuous" if r["disc"] else ""
        if r["key"]:
            if r["n"] < prev:
                flag += "  ← moved"
                moved += 1
            prev = r["n"]
        print(f"- `{r['n']}` **{r['src']}** ↔ {r['eng']}{flag}")
    print(f"\n{moved} of {len(units)} records appear in a different relative order in the target.\n")

    mins = [min(s2t[s] & tset) for s in span if s2t.get(s, set()) & tset]
    inv = sum(1 for a, b in zip(mins, mins[1:]) if b < a)
    shared = collections.Counter(
        frozenset(s2t[s] & tset) for s in span if s2t.get(s, set()) & tset
    )
    print(f"### Correspondence — {inv} of {len(mins)-1} adjacent source units go "
          f"backward in target order\n")
    print("`nothing` = this source unit aligns to no target token. "
          "**bold** = two or more source units share one identical English phrase, "
          "so no token in it belongs to any one of them.\n")
    print("| # | source id | source | gloss | aligned English (target order) |")
    print("|---|---|---|---|---|")
    for i, s in enumerate(span, 1):
        ts = sorted(s2t.get(s, set()) & tset)
        sr = srows.get(s, {})
        if not ts:
            eng = "`nothing`"
        else:
            eng = " ".join(trows[t]["text"] for t in ts)
            if shared[frozenset(ts)] > 1:
                eng = f"**{eng}**"
        print(f"| {i} | `{s}` | {sr.get('text','?')} | {sr.get('gloss','') or '—'} | {eng} |")
    print()
    if unaligned_inside:
        print("### Unaligned tokens inside the span — included, so the text reads properly\n")
        print("| target id | text |")
        print("|---|---|")
        for t in unaligned_inside:
            print(f"| `{t}` | `{trows[t]['text']}` |")
        print()
    if other_unit:
        print("### Covered by the span, but belonging to a different source unit\n")
        print("| target id | text |")
        print("|---|---|")
        for t in other_unit:
            print(f"| `{t}` | {trows[t]['text']} |")
        print()


if __name__ == "__main__":
    print("<!-- Generated by tmp/gen_alignment_demo.py. Regenerate rather than hand-edit. -->")
    print("# Alignment — worked examples\n")
    print("What the ruled operation produces. **R1** — a span returns its aligned tokens plus the")
    print("unaligned tokens between them; a token belonging to a different source unit is not.")
    print("**R5** — the result is ordered by the target's own word order, so the English reads as")
    print("English.\n")
    print("Generated 2026-09-13 from `Clear/Alignments`. Figures are re-derivable with the")
    print("script named in the comment above.\n")
    print("---\n")
    demo("Greek — Luke 1:1–4 (SBLGNT → BSB)", "eng", "BSB", "SBLGNT", "nt", "42", 1, 1, 4,
         note="One periodic Greek sentence spanning four verses — the case where source and "
              "target order come apart hardest.")
    print("---\n")
    demo("Greek — Ephesians 1:3–14 (SBLGNT → BSB)", "eng", "BSB", "SBLGNT", "nt", "49", 1, 3, 14,
         note="A single sentence of roughly two hundred words — the longest in the New "
              "Testament, and heavily restructured in any English rendering.")
    print("---\n")
    print("---\n")
    demo("Hebrew — Psalm 23:1–4 (WLCM → BSB)", "eng", "BSB", "WLCM", "ot", "19", 23, 1, 4,
         note="**This case exposes a systematic gap, and the span below is wrong because of it.** "
              "The Hebrew superscription מִזְמוֹר לְדָוִד is part of Hebrew verse 1. BSB renders "
              "it as a psalm title, and the target file carries that title as tokens numbered "
              "**verse 000** — `19023000001`–`005`, reading A Psalm of David. Neither side is "
              "aligned to the other, so the three Hebrew morphemes report as aligning to nothing "
              "while their English sits in the file unclaimed. Because a span's bounds start "
              "at the first *aligned* token, verse 000 falls outside it and the title is dropped "
              "silently — content present on both sides that the operation cannot reach. "
              "**116 of the 150 psalms carry a verse-000 title, 1,303 tokens in all**, and verse "
              "000 appears in no other book of the Old Testament. The Captain notes this is "
              "common in English translations of the Psalms, so it is a class of case rather "
              "than one psalm. Whether a span over Hebrew verse 1 should reach into target verse "
              "000 is an open decision, not something to settle by silence.")
    print("---\n")
    demo("Hebrew — Ruth 1:1–4 (WLCM → BSB)", "eng", "BSB", "WLCM", "ot", "08", 1, 1, 4,
         note="Hebrew source ids address **morphemes**, not words, so one Hebrew word is often "
              "several source units. Hebrew is right-to-left and has no italic tradition; it is "
              "never italicised here, and bold is a weight rather than a slant.")
