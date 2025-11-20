<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.crosswire.org/2013/TEIOSIS/namespace"
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns:map="http://www.w3.org/2005/xpath-functions/map"
  xmlns:local="urn:local-functions" exclude-result-prefixes="tei xs map local">

  <xsl:output method="json" encoding="UTF-8" indent="yes"/>

  <xsl:function name="local:concat-text" as="xs:string">
    <!-- filepath: /Users/jonathan/github/nida-institute/LLMFlow/xslt/extract-base-json.xslt -->
    <xsl:param name="left" as="xs:string"/>
    <xsl:param name="right" as="xs:string"/>
    <xsl:sequence select="
      if ($left = '' or $right = '') then concat($left, $right)
      else if (matches($left, '[\(\[\{/-]$')) then concat($left, $right)
      else if (matches($right, '^[\),.;:!?·\]\}]')) then concat($left, $right)
      else concat($left, ' ', $right)
    "/>
  </xsl:function>

  <xsl:function name="local:normalize-text" as="xs:string">
    <xsl:param name="value" as="xs:string"/>
    <xsl:variable name="collapsed" select="replace(normalize-space($value), '\.\s*\.\s*\.', '...')"/>
    <xsl:variable name="tightened" select="replace($collapsed, '\s+([,.;:!?·)\]\}])', '$1')"/>
    <xsl:variable name="trimmed-opens" select="replace($tightened, '([\(\[\{«])\s+', '$1')"/>
    <xsl:variable name="spaced-ellipsis" select="replace($trimmed-opens, '(\S)\.\.\.(\S)', '$1 ... $2')"/>
    <xsl:variable name="spaced-punct" select="replace($spaced-ellipsis, '([,;:])([^\s])', '$1 $2')"/>
    <xsl:variable name="deduped" select="replace($spaced-punct, '([,;:])\s*\1+', '$1')"/>
    <xsl:variable name="trimmed-tail" select="replace($deduped, '[:;,]\s*$', '')"/>
    <xsl:sequence select="if (matches($trimmed-tail, '^[,;]+$')) then '' else $trimmed-tail"/>
  </xsl:function>

  <xsl:function name="local:annotate-text" as="map(xs:string, item()*)">
    <xsl:param name="value" as="xs:string"/>
    <xsl:variable name="trimmed" select="normalize-space($value)"/>
    <xsl:variable name="label-match" select="analyze-string($trimmed, '^\s*([A-Za-z][^,:;]+)[,:]\s+(.*)$')"/>
    <xsl:variable name="after-label" select="if ($label-match/*:match)
                          then normalize-space($label-match/*:match/*:group[@nr='2'])
                          else $trimmed"/>
    <xsl:variable name="greek-match"
                  select="analyze-string(
                    $after-label,
                    '^\s*([\p{IsGreek}\p{IsHebrew}·ʼ…]+(?:\s+[\p{IsGreek}\p{IsHebrew}·ʼ…]+)*)\s+(.*)$'
                  )"/>
    <xsl:sequence select="map:merge((
      map{'text': $trimmed},
      if ($label-match/*:match)
        then map{'label': normalize-space($label-match/*:match/*:group[@nr='1'])}
        else map{},
      if ($greek-match/*:match)
        then map{
               'greek': normalize-space($greek-match/*:match/*:group[@nr='1']),
               'gloss': normalize-space($greek-match/*:match/*:group[@nr='2'])
             }
        else map{}
    ))"/>
  </xsl:function>

  <xsl:function name="local:clean-sense-id" as="xs:string">
    <xsl:param name="value" as="xs:string?"/>
    <xsl:sequence select="
      if ($value)
      then replace(normalize-space($value), '\.+$', '')
      else ''
    "/>
  </xsl:function>

  <xsl:function name="local:clean-sense-path" as="xs:string">
    <xsl:param name="value" as="xs:string?"/>
    <xsl:sequence select="
      if ($value)
      then replace(replace(normalize-space($value), '\.{2,}', '.'), '\.$', '')
      else ''
    "/>
  </xsl:function>

  <xsl:function name="local:cleanup-fragments" as="map(xs:string, item()*)*">
    <xsl:param name="items" as="map(xs:string, item()*)*"/>
    <xsl:variable name="non-empty" as="map(xs:string, item()*)*">
      <xsl:for-each select="$items">
        <xsl:variable name="item" select="."/>
        <xsl:variable name="text" select="
          if (map:contains($item, 'text'))
          then normalize-space(string(map:get($item, 'text')))
          else ''
        "/>
        <xsl:if test="not(map:contains($item, 'text') and $text = '')">
          <xsl:sequence select="$item"/>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>
    <xsl:variable name="filtered" as="map(xs:string, item()*)*">
      <xsl:for-each select="$non-empty">
        <xsl:variable name="item" select="."/>
        <xsl:variable name="type" select="string(map:get($item, 'type'))"/>
        <xsl:variable name="text" select="normalize-space(string(map:get($item, 'text')))"/>
        <xsl:variable name="duplicate-gloss" select="
          $type = 'gloss' and $text != '' and
          exists(
            subsequence($non-empty, 1, position() - 1)
            [string(map:get(., 'type')) = 'gloss' and
             normalize-space(string(map:get(., 'text'))) = $text]
          )
        "/>
        <xsl:if test="not($duplicate-gloss)">
          <xsl:sequence select="$item"/>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>
    <xsl:sequence select="$filtered"/>
  </xsl:function>

  <xsl:function name="local:coalesce-content" as="map(xs:string, item()*)*">
    <xsl:param name="items" as="map(xs:string, item()*)*"/>
    <xsl:sequence select="local:cleanup-fragments($items)"/>
  </xsl:function>

  <xsl:function name="local:join-markdown" as="xs:string">
    <xsl:param name="items" as="map(xs:string, item()*)*"/>
    <xsl:param name="separator" as="xs:string"/>
    <xsl:variable name="sep" select="if (exists($separator)) then $separator else ' '"/>
    <xsl:sequence select="
      if (empty($items)) then ''
      else string-join(for $i in $items return string(map:get($i, 'markdown')), $sep)
    "/>
  </xsl:function>

  <xsl:template match="/tei:entry">
    <!-- filepath: /Users/jonathan/github/nida-institute/LLMFlow/xslt/extract-base-json.xslt -->
    <xsl:variable name="form" as="map(xs:string, item()*)*">
      <xsl:apply-templates select="tei:form" mode="form"/>
    </xsl:variable>

    <xsl:variable name="pos" as="map(xs:string, item()*)*">
      <xsl:apply-templates select="tei:gramGrp" mode="pos"/>
    </xsl:variable>

    <xsl:variable name="etym" as="map(xs:string, item()*)">
      <xsl:sequence select="
        if (tei:etym)
        then map{ 'etymology': normalize-space(tei:etym) }
        else map{}
      "/>
    </xsl:variable>

    <xsl:variable name="entry-inline-items" as="map(xs:string, item()*)*">
      <xsl:apply-templates select="node()[not(self::tei:form or self::tei:gramGrp or self::tei:etym or self::tei:sense or (self::tei:note[@type='occurrencesNT']))]" mode="content"/>
    </xsl:variable>
    <xsl:variable name="entry-inline" select="local:coalesce-content($entry-inline-items)"/>

    <xsl:variable name="senses" as="map(xs:string, item()*)*">
      <xsl:apply-templates select="tei:sense" mode="sense"/>
    </xsl:variable>

    <xsl:sequence select="
      map:merge((
        map{ 'lemma': string(@n) },
        map{ 'strongsNumber': local:clean-sense-id(string(@n)) },
        if (tei:note[@type='occurrencesNT'])
          then map{ 'occurrencesNT': xs:integer(tei:note[@type='occurrencesNT']) }
          else map{},
        if (exists($form)) then map:merge($form) else map{},
        if (exists($pos)) then map:merge($pos) else map{},
        $etym,
        if (exists($entry-inline))
          then map{ 'content': array{ $entry-inline } }
          else map{},
        map{ 'senses': array{ $senses } }
      ))
    "/>
  </xsl:template>

  <xsl:template match="tei:form" mode="form" as="map(xs:string, item()*)">
    <xsl:sequence select="
      map:merge((
        map{ 'form': normalize-space(tei:orth) },
        if (tei:foreign)
          then map{
            'formVariants': array{
              for $f in tei:foreign return normalize-space($f)
            }
          }
          else map{}
      ))
    "/>
  </xsl:template>

  <xsl:template match="tei:gramGrp" mode="pos" as="map(xs:string, item()*)">
    <xsl:sequence select="
      map:merge((
        map{ 'pos': normalize-space(tei:pos) },
        if (tei:foreign)
          then map{ 'posGreek': normalize-space(tei:foreign) }
          else map{}
      ))
    "/>
  </xsl:template>

  <xsl:template match="tei:sense" mode="sense" as="map(xs:string, item()*)">
    <xsl:variable name="label-node" as="node()?">
      <xsl:sequence select="text()[not(preceding-sibling::*)][1]"/>
    </xsl:variable>

    <xsl:variable name="label" as="xs:string" select="if ($label-node) then normalize-space($label-node) else ''"/>

    <xsl:variable name="direct-glosses" select="tei:gloss[not(parent::tei:usageGroup)]"/>

    <xsl:variable name="usageGroups" as="map(xs:string, item()*)*">
      <xsl:apply-templates select="tei:usageGroup" mode="usage-group"/>
    </xsl:variable>

    <xsl:variable name="subsenses" as="map(xs:string, item()*)*">
      <xsl:apply-templates select="tei:sense" mode="sense"/>
    </xsl:variable>

    <xsl:variable name="extra-content" as="map(xs:string, item()*)*">
      <xsl:apply-templates select="node()[not(. is $label-node)
                       and not(self::tei:sense)
                       and not(self::tei:usageGroup)]" mode="content">
        <xsl:with-param name="skip-node" select="$label-node" tunnel="yes"/>
      </xsl:apply-templates>
    </xsl:variable>

    <xsl:variable name="label-items" as="map(xs:string, item()*)*">
      <xsl:sequence select="
        if ($label-node)
        then (
          let $annot := local:annotate-text(local:normalize-text(string($label-node)))
          return map:merge((
            map{ 'text': map:get($annot, 'text') },
            map:remove($annot, 'text')
          ))
        )
        else ()
      "/>
      </xsl:variable>
      <xsl:variable name="content-items" as="map(xs:string, item()*)*">
        <xsl:sequence select="($label-items, $extra-content)"/>
      </xsl:variable>
      <xsl:variable name="merged-content" select="local:coalesce-content($content-items)"/>
      <xsl:sequence select="
      map:merge((
        map{ 'id': local:clean-sense-id(string(@n)) },
        map{ 'path': local:clean-sense-path(string(@sensePath)) },
        if ($label != '' and not(matches($label, '^[,:;.]+$')))
          then map{ 'label': replace($label, '[,:;.]+$', '') }
          else map{},
        if (exists($direct-glosses))
          then
            if (count($direct-glosses) = 1)
            then map{ 'gloss': normalize-space($direct-glosses[1]) }
            else map{ 'glosses': array{ $direct-glosses ! normalize-space(.) } }
          else map{},
        if (exists($merged-content))
          then map{ 'content': array{ $merged-content } }
          else map{},
        if (exists($usageGroups))
          then map{ 'usageGroups': array{ $usageGroups } }
          else map{},
        if (exists($subsenses))
          then map{ 'subsenses': array{ $subsenses } }
          else map{}
      ))
    "/>
    </xsl:template>

    <xsl:template match="tei:usageGroup" mode="usage-group" as="map(xs:string, item()*)">
      <xsl:variable name="content-raw" as="map(xs:string, item()*)*">
        <xsl:apply-templates mode="content"/>
      </xsl:variable>
      <xsl:variable name="content" select="local:coalesce-content($content-raw)"/>
      <xsl:sequence select="map:merge((
        map{
          'type': 'usageGroup',
          'path': string(@sensePath),
          'content': array{ $content }
        },
        if (@type) then map{'usageType': string(@type)} else map{}
      ))"/>
    </xsl:template>

    <xsl:template match="text()" mode="content" as="map(xs:string, item()*)?">
      <xsl:variable name="normalized" select="local:normalize-text(.)"/>
      <xsl:if test="$normalized != ''">
        <xsl:variable name="annotated" select="local:annotate-text($normalized)"/>
        <xsl:variable name="has-label" select="map:contains($annotated, 'label')"/>
        <xsl:variable name="has-gloss" select="map:contains($annotated, 'gloss')"/>
        <xsl:variable name="markdown" select="
          if ($has-gloss)
          then concat('`', string(map:get($annotated, 'greek')), '` — _', string(map:get($annotated, 'gloss')), '_')
          else if ($has-label)
          then concat('**', string(map:get($annotated, 'text')), '**')
          else string(map:get($annotated, 'text'))
        "/>
        <xsl:variable name="base" select="map{
          'type': if ($has-gloss) then 'glossed-text'
                  else if ($has-label) then 'label'
                  else 'text',
          'text': map:get($annotated, 'text'),
          'markdown': $markdown
        }"/>
        <xsl:sequence select="map:merge((
          $base,
          map:remove($annotated, 'text')
        ))"/>
      </xsl:if>
    </xsl:template>

    <xsl:template match="tei:foreign" mode="content" as="map(xs:string, item()*)">
      <xsl:variable name="value" select="normalize-space(.)"/>
      <xsl:sequence select="map:merge((
      map{
        'type': 'foreign',
        'role': 'source',
        'text': $value,
        'markdown': concat('`', $value, '`')
       },
       if (@xml:lang) then map{'lang': string(@xml:lang)} else map{},
       if (@type) then map{'foreignType': string(@type)} else map{}
     ))"/>
    </xsl:template>

    <xsl:template match="tei:gloss" mode="content" as="map(xs:string, item()*)">
      <xsl:variable name="value" select="normalize-space(.)"/>
      <xsl:sequence select="map{
        'type': 'gloss',
        'role': 'gloss',
        'text': $value,
        'markdown': concat('_', $value, '_')
      }"/>
    </xsl:template>

    <xsl:template match="tei:quote" mode="content" as="map(xs:string, item()*)">
      <xsl:variable name="parts" as="map(xs:string, item()*)*">
        <xsl:apply-templates select="node()" mode="content"/>
      </xsl:variable>
      <xsl:sequence select="map:merge((
        map{
          'type': 'quote',
          'content': array{ $parts },
          'markdown': concat('> ', local:join-markdown($parts, ' '))
        },
        if (@xml:lang) then map{'lang': string(@xml:lang)} else map{},
        if (@type) then map{'quoteType': string(@type)} else map{}
      ))"/>
    </xsl:template>

    <xsl:template match="tei:seg" mode="content" as="map(xs:string, item()*)">
      <xsl:variable name="parts" as="map(xs:string, item()*)*">
        <xsl:apply-templates select="node()" mode="content"/>
      </xsl:variable>
      <xsl:sequence select="map:merge((
        map{
          'type': 'segment',
          'content': array{ $parts },
          'markdown': local:join-markdown($parts, ' ')
        },
        if (@type) then map{'segType': string(@type)} else map{}
      ))"/>
    </xsl:template>

    <xsl:template match="tei:ref[@osisRef]" mode="content" as="map(xs:string, item()*)">
      <xsl:variable name="note-text" select="normalize-space(following-sibling::text()[1])"/>
      <xsl:variable name="note" select="if (matches($note-text, '^\([^)]+\)'))
                           then replace($note-text, '^\(([^)]+)\).*', '$1')
                           else ''"/>
      <xsl:sequence select="map:merge((
       map{
         'type': 'reference',
         'text': normalize-space(.),
         'reference': string(@osisRef),
         'markdown': concat(normalize-space(.), ' (`', string(@osisRef), '`)')
       },
       if ($note != '') then map{'note': $note} else map{}
     ))"/>
    </xsl:template>

    <xsl:template match="tei:ref[not(@osisRef)]" mode="content" as="map(xs:string, item()*)">
      <xsl:variable name="value" select="normalize-space(.)"/>
      <xsl:sequence select="map{
      'type': 'citation',
      'text': $value,
      'markdown': concat('_', $value, '_')
    }"/>
    </xsl:template>

    <xsl:template match="tei:note" mode="content" as="map(xs:string, item()*)">
    <xsl:variable name="value" select="normalize-space(.)"/>
    <xsl:sequence select="map:merge((
      map{
        'type': 'note',
        'text': $value,
        'markdown': concat('> ', $value)
      },
       if (@type) then map{'noteType': string(@type)} else map{},
       if (@xml:lang) then map{'noteLang': string(@xml:lang)} else map{}
     ))"/>
    </xsl:template>

    <xsl:template match="tei:emph" mode="content" as="map(xs:string, item()*)">
    <xsl:variable name="value" select="normalize-space(.)"/>
    <xsl:sequence select="map{
      'type': 'emphasis',
      'text': $value,
      'markdown': concat('*', $value, '*')
    }"/>
    </xsl:template>

    <xsl:template match="tei:usageGroup" mode="usage-group" as="map(xs:string, item()*)">
     <xsl:variable name="content-raw" as="map(xs:string, item()*)*">
       <xsl:apply-templates mode="content"/>
     </xsl:variable>
     <xsl:variable name="content" select="local:coalesce-content($content-raw)"/>
     <xsl:sequence select="map:merge((
       map{
         'type': 'usageGroup',
         'path': string(@sensePath),
         'content': array{ $content },
         'markdown': local:join-markdown($content, ' ')
       },
       if (@type) then map{'usageType': string(@type)} else map{}
     ))"/>
   </xsl:template>

    <xsl:template match="*" mode="content" as="map(xs:string, item()*)?">
      <xsl:message>
      Warning: Unhandled element in content: <xsl:value-of select="local-name()"/>
      </xsl:message>
      <xsl:sequence select="()"/>
    </xsl:template>

  </xsl:stylesheet>

