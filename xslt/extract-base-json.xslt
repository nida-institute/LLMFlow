<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.crosswire.org/2013/TEIOSIS/namespace"
  xmlns:local="http://local.functions"
  xmlns:map="http://www.w3.org/2005/xpath-functions/map"
  xmlns:array="http://www.w3.org/2005/xpath-functions/array"
  exclude-result-prefixes="tei local map array">

  <xsl:output method="text" encoding="UTF-8" media-type="application/json"/>


  <xsl:variable name="newline" select="'&#10;'"/>

  <xsl:template match="/tei:entry">
    <xsl:variable name="json-map" select="
      map {
        'lemma': string(@key),
        'schemaVersion': 'base.v4.structural',
        'segments': array { local:collect-segments(.) },
        'senses': array { local:collect-senses(.) },
        'forms': array { local:collect-forms(.) },
        'warnings': array {},
        'notes': array { local:collect-notes(.) }
      }
    "/>

    <xsl:value-of select="serialize($json-map, map{'method':'json','indent':true()})"/>
  </xsl:template>

  <!-- Collect all segments from sense content -->
  <xsl:function name="local:collect-segments">
    <xsl:param name="entry"/>
    <xsl:variable name="index" select="0"/>
    <xsl:sequence select="local:process-node-for-segments($entry, $index)"/>
  </xsl:function>

  <xsl:function name="local:process-node-for-segments">
    <xsl:param name="node"/>
    <xsl:param name="index"/>

    <xsl:variable name="sensePath" select="
      if ($node/ancestor-or-self::tei:sense[@sensePath])
      then $node/ancestor-or-self::tei:sense[@sensePath][1]/@sensePath
      else ''
    "/>

    <xsl:choose>
      <!-- Gloss -->
      <xsl:when test="$node/self::tei:gloss">
        <xsl:sequence select="map {
          'index': $index,
          'type': 'gloss',
          'text': normalize-space($node),
          'sensePath': string($sensePath)
        }"/>
      </xsl:when>

      <!-- Foreign -->
      <xsl:when test="$node/self::tei:foreign">
        <xsl:sequence select="map {
          'index': $index,
          'type': 'foreign',
          'text': normalize-space($node),
          'lang': string($node/@xml:lang),
          'sensePath': string($sensePath)
        }"/>
      </xsl:when>

      <!-- Ref -->
      <xsl:when test="$node/self::tei:ref">
        <xsl:sequence select="map {
          'index': $index,
          'type': 'ref',
          'text': normalize-space($node),
          'osisRef': string($node/@osisRef),
          'sensePath': string($sensePath)
        }"/>
      </xsl:when>

      <!-- UsageGroup - process children -->
      <xsl:when test="$node/self::tei:usageGroup">
        <xsl:for-each select="$node/node()">
          <xsl:sequence select="local:process-node-for-segments(., $index + position() - 1)"/>
        </xsl:for-each>
      </xsl:when>

      <!-- Sense - process children (skip nested senses for now) -->
      <xsl:when test="$node/self::tei:sense">
        <xsl:for-each select="$node/node()[not(self::tei:sense)]">
          <xsl:sequence select="local:process-node-for-segments(., $index + position() - 1)"/>
        </xsl:for-each>
        <!-- Then process nested senses -->
        <xsl:for-each select="$node/tei:sense">
          <xsl:sequence select="local:process-node-for-segments(., $index + position() - 1)"/>
        </xsl:for-each>
      </xsl:when>

      <!-- Text nodes -->
      <xsl:when test="$node/self::text() and normalize-space($node) != ''">
        <xsl:sequence select="map {
          'index': $index,
          'type': 'senseProse',
          'text': normalize-space($node),
          'sensePath': string($sensePath)
        }"/>
      </xsl:when>

      <!-- Entry - process all children -->
      <xsl:when test="$node/self::tei:entry">
        <xsl:for-each select="$node//tei:sense">
          <xsl:sequence select="local:process-node-for-segments(., position() - 1)"/>
        </xsl:for-each>
      </xsl:when>
    </xsl:choose>
  </xsl:function>

  <!-- Collect sense paths -->
  <xsl:function name="local:collect-senses">
    <xsl:param name="entry"/>
    <xsl:for-each select="$entry//tei:sense[@sensePath]">
      <xsl:sequence select="map {
        'sensePath': string(@sensePath),
        'n': string(@n)
      }"/>
    </xsl:for-each>
  </xsl:function>

  <!-- Collect forms -->
  <xsl:function name="local:collect-forms">
    <xsl:param name="entry"/>
    <xsl:for-each select="$entry/tei:form">
      <xsl:sequence select="map {
        'orth': normalize-space(tei:orth),
        'variants': array {
          for $f in tei:foreign
          return normalize-space($f)
        }
      }"/>
    </xsl:for-each>
  </xsl:function>

  <!-- Collect notes -->
  <xsl:function name="local:collect-notes">
    <xsl:param name="entry"/>
    <xsl:for-each select="$entry/tei:note">
      <xsl:sequence select="map {
        'type': string(@type),
        'text': normalize-space(.)
      }"/>
    </xsl:for-each>
  </xsl:function>

</xsl:stylesheet>
