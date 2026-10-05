(: Lemma frequency for the Greek New Testament, from the Macula Greek Lowfat trees.

   One entry per lemma: how many words carry it, and the smallest N for which it falls among the
   least frequent N% of lemmas — so a word is less common at a cut-off of N when
   `in_least_frequent_percent <= N`.

   Read from a BaseX database of the Lowfat directory rather than from the files: Luke's trees
   nest 101 elements deep, and parsing the file directly stops at the JDK's limit of 100.

   Regenerate:
     basex -b database=SBLGNT-lowfat -o data/lemma-frequency-greek.json tools/lemma-frequency/greek.xq

   The table is read by `include: [frequency]` on a `type: scripture` step. :)

declare option output:method "json";

declare variable $database external;

let $words := collection($database)//w
let $entries :=
  for $w in $words
  group by $lemma := string($w/@lemma)
  return map { 'lemma': $lemma, 'count': count($w) }
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
      <corpus>SBLGNT, Macula Greek Lowfat</corpus>
      <unit>word (w)</unit>
      <words type="number">{ count($words) }</words>
      <lemmas type="number">{ $total }</lemmas>
      <query>tools/lemma-frequency/greek.xq</query>
    </about>
    <lemmas type="array">{
      for $e in $entries
      order by $e?count descending, $e?lemma
      return
        <_ type="object">
          <lemma>{ $e?lemma }</lemma>
          <count type="number">{ $e?count }</count>
          <in__least__frequent__percent type="number">{
            round-half-to-even(100 * $cumulative($e?count) div $total, 2)
          }</in__least__frequent__percent>
        </_>
    }</lemmas>
  </json>
