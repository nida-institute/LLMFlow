(: acai-verse-range.xq
   Return all ACAI entities that have at least one reference within a
   chapter range of a given book.

   Parameters (injected by the basex step via str.format_map):
     {db}           — BaseX database name (default: "acai")
     {book_id}      — OSIS book code, e.g. "MAT", "GEN"
     {start_chapter} — first chapter (integer string), inclusive
     {end_chapter}   — last chapter  (integer string), inclusive

   Usage in a pipeline YAML step:
     type: basex
     query_file: queries/acai-verse-range.xq
     params:
       db: acai
       book_id: "${book_id}"
       start_chapter: "${chapter}"
       end_chapter: "${chapter}"

   NOTE: The exact element/attribute names below reflect the ACAI XML
   structure expected after 'sp load-db basex acai'.  If ACAI ships as
   JSON/Markdown, convert to XML first (or adapt this query to POST via
   the BaseX REST API with a JSON serializer).
:)

let $entities :=
  for $e in db:get("{db}")//entity
  where some $r in $e/references/ref satisfies (
    $r/@book = "{book_id}" and
    xs:integer($r/@chapter) >= {start_chapter} and
    xs:integer($r/@chapter) <= {end_chapter}
  )
  return $e

return
  <results book="{book_id}" start="{start_chapter}" end="{end_chapter}"
           count="{{ count($entities) }}">
    {{ $entities }}
  </results>
