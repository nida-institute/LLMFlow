<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.crosswire.org/2013/TEIOSIS/namespace"
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns:local="http://local.functions"
  xmlns:map="http://www.w3.org/2005/xpath-functions/map"
  xmlns:array="http://www.w3.org/2005/xpath-functions/array">

  <xsl:output method="text" encoding="UTF-8" media-type="application/json"/>

  <xsl:variable name="newline" select="'&#10;'"/>

  <xsl:template match="/tei:entry">
    <xsl:variable name="json-map" select="
      map {
        'lemma': string(@key),
        'pos': string(@pos),
        'etymology': local:get-etymology(.),
        'segments': array { local:collect-segments(.) }
      }
    "/>

    <xsl:value-of select="serialize($json-map, map{'method':'json','indent':true()})"/>
  </xsl:template>

  <!-- Extract etymology if present -->
  <xsl:function name="local:get-etymology" as="xs:string">
    <xsl:param name="entry"/>
    <xsl:sequence select="
      if ($entry/tei:etym)
      then normalize-space($entry/tei:etym)
      else ''
    "/>
  </xsl:function>

  <!-- Collect all segments from sense content -->
  <xsl:function name="local:collect-segments">
    <xsl:param name="entry"/>
    <xsl:sequence select="local:process-sense-tree($entry, 0)"/>
  </xsl:function>

  <!-- Process all senses in document order -->
  <xsl:function name="local:process-sense-tree">
    <xsl:param name="node"/>
    <xsl:param name="start-index" as="xs:integer"/>

    <xsl:variable name="all-content" as="item()*">
      <xsl:for-each select="$node//tei:sense">
        <xsl:sequence select="local:process-sense-content(.)"/>
      </xsl:for-each>
    </xsl:variable>

    <!-- Add sequential indices -->
    <xsl:for-each select="$all-content">
      <xsl:variable name="current-map" select="."/>
      <xsl:sequence select="map:put($current-map, 'index', $start-index + position() - 1)"/>
    </xsl:for-each>
  </xsl:function>

  <!-- Process content within a single sense -->
  <xsl:function name="local:process-sense-content">
    <xsl:param name="sense"/>

    <xsl:variable name="sensePath" select="string($sense/@sensePath)"/>

    <!-- Process all child nodes except nested senses -->
    <xsl:for-each select="$sense/node()[not(self::tei:sense)]">
      <xsl:sequence select="local:node-to-segment(., $sensePath)"/>
    </xsl:for-each>
  </xsl:function>

  <!-- Convert individual node to segment -->
  <xsl:function name="local:node-to-segment">
    <xsl:param name="node"/>
    <xsl:param name="sensePath" as="xs:string"/>

    <xsl:choose>
      <!-- Gloss -->
      <xsl:when test="$node/self::tei:gloss">
        <xsl:sequence select="map {
          'text': normalize-space($node),
          'type': 'gloss',
          'lang': 'eng',
          'sensePath': $sensePath
        }"/>
      </xsl:when>

      <!-- Foreign (Greek text) -->
      <xsl:when test="$node/self::tei:foreign">
        <xsl:sequence select="map {
          'text': normalize-space($node),
          'type': 'foreign',
          'lang': string($node/@xml:lang),
          'sensePath': $sensePath
        }"/>
      </xsl:when>

      <!-- Biblical reference -->
      <xsl:when test="$node/self::tei:ref[@osisRef]">
        <xsl:sequence select="map {
          'text': normalize-space($node),
          'type': 'ref',
          'lang': 'eng',
          'osisRef': string($node/@osisRef),
          'sensePath': $sensePath
        }"/>
      </xsl:when>

      <!-- Grammar/lexicon reference (no osisRef) -->
      <xsl:when test="$node/self::tei:ref[not(@osisRef)]">
        <xsl:sequence select="map {
          'text': normalize-space($node),
          'type': 'citation',
          'lang': 'eng',
          'sensePath': $sensePath
        }"/>
      </xsl:when>

      <!-- UsageGroup - process children -->
      <xsl:when test="$node/self::tei:usageGroup">
        <xsl:for-each select="$node/node()">
          <xsl:sequence select="local:node-to-segment(., $sensePath)"/>
        </xsl:for-each>
      </xsl:when>

      <!-- Text nodes (prose definitions) -->
      <xsl:when test="$node/self::text() and normalize-space($node) != ''">
        <xsl:sequence select="map {
          'text': normalize-space($node),
          'type': 'senseProse',
          'lang': 'eng',
          'sensePath': $sensePath
        }"/>
      </xsl:when>
    </xsl:choose>
  </xsl:function>

</xsl:stylesheet>
