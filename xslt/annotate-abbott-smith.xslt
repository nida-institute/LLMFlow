<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.crosswire.org/2013/TEIOSIS/namespace"
  xmlns:local="http://local.functions"
  xmlns="http://www.crosswire.org/2013/TEIOSIS/namespace"
  exclude-result-prefixes="tei local">

  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

  <!-- Default: copy everything as-is -->
  <xsl:template match="@* | node()">
    <xsl:copy>
      <xsl:apply-templates select="@* | node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- Build sense path from ancestor @n attributes -->
  <xsl:function name="local:sense-path">
    <xsl:param name="sense"/>
    <xsl:variable name="parts" select="$sense/ancestor-or-self::tei:sense/@n"/>
    <xsl:value-of select="string-join($parts, '.')"/>
  </xsl:function>

  <!-- Process each sense: add sensePath and create normalized node sequence -->
  <xsl:template match="tei:sense">
    <xsl:variable name="path" select="local:sense-path(.)"/>

    <!-- First pass: normalize text nodes by splitting on semicolons/colons -->
    <xsl:variable name="normalized-nodes">
      <xsl:apply-templates select="node()" mode="normalize-text"/>
    </xsl:variable>

    <xsl:copy>
      <!-- Copy all attributes including @n -->
      <xsl:apply-templates select="@*"/>
      <!-- Add sensePath attribute -->
      <xsl:attribute name="sensePath" select="$path"/>

      <!-- Second pass: group the normalized nodes -->
      <xsl:call-template name="group-by-punctuation">
        <xsl:with-param name="nodes" select="$normalized-nodes/node()"/>
        <xsl:with-param name="sensePath" select="$path"/>
      </xsl:call-template>
    </xsl:copy>
  </xsl:template>

  <!-- Mode: normalize text nodes ONLY (don't touch element content) -->
  <xsl:template match="text()" mode="normalize-text">
    <!-- Only split if we're in direct sense content, not inside foreign/ref/etc -->
    <xsl:choose>
      <xsl:when test="parent::tei:sense">
        <!-- Split on semicolons and colons (but NOT periods) -->
        <xsl:analyze-string select="." regex="([^;:]+)([;:])">
          <xsl:matching-substring>
            <!-- Text before punctuation -->
            <xsl:value-of select="regex-group(1)"/>
            <!-- Punctuation as separate marker -->
            <punct><xsl:value-of select="regex-group(2)"/></punct>
          </xsl:matching-substring>
          <xsl:non-matching-substring>
            <xsl:value-of select="."/>
          </xsl:non-matching-substring>
        </xsl:analyze-string>
      </xsl:when>
      <xsl:otherwise>
        <!-- Keep text inside elements unchanged -->
        <xsl:value-of select="."/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Copy elements through in normalize mode, preserving all attributes -->
  <xsl:template match="*" mode="normalize-text">
    <xsl:copy>
      <xsl:apply-templates select="@* | node()" mode="normalize-text"/>
    </xsl:copy>
  </xsl:template>

  <!-- Copy attributes in normalize mode -->
  <xsl:template match="@*" mode="normalize-text">
    <xsl:copy/>
  </xsl:template>

  <!-- Group nodes by <punct> markers -->
  <xsl:template name="group-by-punctuation">
    <xsl:param name="nodes"/>
    <xsl:param name="sensePath"/>

    <xsl:for-each-group select="$nodes"
      group-ending-with="punct">

      <!-- Check if group contains foreign or ref (= usage example) -->
      <xsl:variable name="has-usage" select="
        current-group()[self::tei:foreign] or
        current-group()[self::tei:ref]"/>

      <xsl:choose>
        <!-- Wrap usage examples in usageGroup -->
        <xsl:when test="$has-usage">
          <usageGroup sensePath="{$sensePath}">
            <!-- Output all nodes, converting punct to text -->
            <xsl:for-each select="current-group()">
              <xsl:choose>
                <!-- Convert punct elements to plain text -->
                <xsl:when test="self::punct">
                  <xsl:value-of select="."/>
                </xsl:when>
                <!-- Nested sense elements need special handling -->
                <xsl:when test="self::tei:sense">
                  <xsl:apply-templates select="." mode="#default"/>
                </xsl:when>
                <!-- Everything else copy as-is -->
                <xsl:otherwise>
                  <xsl:copy-of select="."/>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:for-each>
          </usageGroup>
        </xsl:when>

        <!-- Pass through prose/notes as-is -->
        <xsl:otherwise>
          <xsl:for-each select="current-group()">
            <xsl:choose>
              <!-- Convert punct elements to plain text -->
              <xsl:when test="self::punct">
                <xsl:value-of select="."/>
              </xsl:when>
              <!-- Nested sense elements need special handling -->
              <xsl:when test="self::tei:sense">
                <xsl:apply-templates select="." mode="#default"/>
              </xsl:when>
              <!-- Everything else copy as-is -->
              <xsl:otherwise>
                <xsl:copy-of select="."/>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each-group>
  </xsl:template>

</xsl:stylesheet>
