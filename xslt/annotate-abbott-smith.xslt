<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.crosswire.org/2013/TEIOSIS/namespace"
  xmlns:local="http://local.functions"
  xmlns="http://www.crosswire.org/2013/TEIOSIS/namespace"
  exclude-result-prefixes="tei local">

  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

  <!-- Default: copy everything as-is -->
  <xsl:template match="@* | node()">
    <xsl:copy copy-namespaces="no">
      <xsl:apply-templates select="@* | node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- Build sense path from ancestor @n attributes -->
  <xsl:function name="local:sense-path">
    <xsl:param name="sense"/>
    <xsl:variable name="parts" select="$sense/ancestor-or-self::tei:sense/@n"/>
    <xsl:value-of select="string-join($parts, '.')"/>
  </xsl:function>

  <!-- Strip trailing dot from a string -->
  <xsl:function name="local:strip-dot">
    <xsl:param name="text"/>
    <xsl:value-of select="
      if (ends-with($text, '.'))
      then substring($text, 1, string-length($text) - 1)
      else $text"/>
  </xsl:function>

  <!-- Process each sense: add sensePath and handle grouping inline -->
  <xsl:template match="tei:sense">
    <xsl:param name="parent-sensePath" select="''"/>
    
    <!-- Calculate path: if we have a parent path param, use it; otherwise use ancestors -->
    <xsl:variable name="path">
      <xsl:choose>
        <xsl:when test="$parent-sensePath != ''">
          <!-- We're a nested sense from a fragment, build path from parent + our @n -->
          <xsl:value-of select="concat(
            local:strip-dot($parent-sensePath),
            '.',
            local:strip-dot(@n))"/>
        </xsl:when>
        <xsl:otherwise>
          <!-- We're a top-level sense in original doc, use ancestor axis -->
          <xsl:value-of select="local:sense-path(.)"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    
    <xsl:copy copy-namespaces="no">
      <xsl:apply-templates select="@*"/>
      <xsl:attribute name="sensePath" select="$path"/>
      
      <!-- Process children, grouping by punctuation -->
      <xsl:call-template name="process-sense-content">
        <xsl:with-param name="nodes" select="node()"/>
        <xsl:with-param name="sensePath" select="$path"/>
      </xsl:call-template>
    </xsl:copy>
  </xsl:template>

  <!-- Process sense content: group text by semicolons/colons, wrap usage examples -->
  <xsl:template name="process-sense-content">
    <xsl:param name="nodes"/>
    <xsl:param name="sensePath"/>
    
    <!-- Split text nodes and group the result -->
    <xsl:variable name="split-nodes">
      <xsl:for-each select="$nodes">
        <xsl:choose>
          <!-- Text directly in sense: split on : and ; -->
          <xsl:when test="self::text() and parent::tei:sense">
            <xsl:analyze-string select="." regex="([^;:]+)([;:])">
              <xsl:matching-substring>
                <xsl:value-of select="regex-group(1)"/>
                <marker type="punct"><xsl:value-of select="regex-group(2)"/></marker>
              </xsl:matching-substring>
              <xsl:non-matching-substring>
                <xsl:value-of select="."/>
              </xsl:non-matching-substring>
            </xsl:analyze-string>
          </xsl:when>
          <!-- Everything else pass through as-is -->
          <xsl:otherwise>
            <xsl:sequence select="."/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
    </xsl:variable>
    
    <!-- Group by marker elements -->
    <xsl:for-each-group select="$split-nodes/node()" 
      group-ending-with="marker[@type='punct']">
      
      <xsl:variable name="has-usage" select="
        current-group()[self::tei:foreign] or 
        current-group()[self::tei:ref]"/>
      
      <xsl:choose>
        <!-- Wrap usage examples -->
        <xsl:when test="$has-usage">
          <usageGroup sensePath="{$sensePath}">
            <xsl:for-each select="current-group()">
              <xsl:choose>
                <!-- Convert markers to text -->
                <xsl:when test="self::marker[@type='punct']">
                  <xsl:value-of select="."/>
                </xsl:when>
                <!-- Nested senses - pass parent path -->
                <xsl:when test="self::tei:sense">
                  <xsl:apply-templates select=".">
                    <xsl:with-param name="parent-sensePath" select="$sensePath"/>
                  </xsl:apply-templates>
                </xsl:when>
                <!-- Everything else -->
                <xsl:otherwise>
                  <xsl:apply-templates select="." mode="copy-clean"/>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:for-each>
          </usageGroup>
        </xsl:when>
        
        <!-- Pass through prose -->
        <xsl:otherwise>
          <xsl:for-each select="current-group()">
            <xsl:choose>
              <!-- Convert markers to text -->
              <xsl:when test="self::marker[@type='punct']">
                <xsl:value-of select="."/>
              </xsl:when>
              <!-- Nested senses - pass parent path -->
              <xsl:when test="self::tei:sense">
                <xsl:apply-templates select=".">
                  <xsl:with-param name="parent-sensePath" select="$sensePath"/>
                </xsl:apply-templates>
              </xsl:when>
              <!-- Everything else -->
              <xsl:otherwise>
                <xsl:apply-templates select="." mode="copy-clean"/>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each-group>
  </xsl:template>

  <!-- Mode: copy without namespaces -->
  <xsl:template match="*" mode="copy-clean">
    <xsl:copy copy-namespaces="no">
      <xsl:apply-templates select="@* | node()" mode="copy-clean"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="@* | text()" mode="copy-clean">
    <xsl:copy/>
  </xsl:template>

</xsl:stylesheet>
