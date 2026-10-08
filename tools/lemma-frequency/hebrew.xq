(: Lemma frequency for the Hebrew Bible, from the Macula Hebrew Lowfat trees.

   The unit is the morpheme (m), leaving out pronominal suffixes (pos="suffix"), which carry the
   lemma of the independent pronoun. Hebrew and Aramaic are counted together; `aramaic` says how
   many of a lemma's occurrences are Aramaic.

   `in_least_frequent_percent` is the smallest N for which the lemma falls among the least
   frequent N% of lemmas — so a word is less common at a cut-off of N when it is `<= N`.

   Read from a BaseX database of the Lowfat directory, as greek.xq is.

   Regenerate:
     basex -b database=macula-hebrew-lowfat -o data/lemma-frequency-hebrew.json tools/lemma-frequency/hebrew.xq

   The table is read by `include: [frequency]` on a `type: scripture` step. :)

declare option output:method "json";

declare variable $database external;

let $morphemes := collection($database)//m[not(@pos = 'suffix')]
let $entries :=
  for $m in $morphemes
  group by $lemma := string($m/@lemma)
  return map { 'lemma': $lemma, 'count': count($m), 'aramaic': count($m[@lang = 'A']) }
let $total := count($entries)
let $ascending :=
  for $e in $entries
  group by $c := $e?count
  order by $c ascending
  return map { 'c': $c, 'n': count($e) }
let $cumulative := fold-left($ascending, [0, map {}], function($acc, $x) {
  let $sum := $acc(1) + $x?n
  return [$sum, map:put($acc(2), $x?c, $sum)]
})(2)
return
  <json type="object">
    <about type="object">
      <corpus>WLC, Macula Hebrew Lowfat</corpus>
      <unit>morpheme (m), pronominal suffixes excluded</unit>
      <morphemes type="number">{ count($morphemes) }</morphemes>
      <lemmas type="number">{ $total }</lemmas>
      <query>tools/lemma-frequency/hebrew.xq</query>
    </about>
    <lemmas type="array">{
      for $e in $entries
      order by $e?count descending, $e?lemma
      return
        <_ type="object">
          <lemma>{ $e?lemma }</lemma>
          <count type="number">{ $e?count }</count>
          <aramaic type="number">{ $e?aramaic }</aramaic>
          <in__least__frequent__percent type="number">{
            round-half-to-even(100 * $cumulative($e?count) div $total, 2)
          }</in__least__frequent__percent>
        </_>
    }</lemmas>
  </json>
