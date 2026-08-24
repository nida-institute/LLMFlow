# Paratext Metadata Schemas

> **Use this file for:** Scripture Burrito field paths, Paratext Settings.xml elements, available metadata fields, constructing XPath queries, understanding project metadata structure.
> **Budget: 150 lines / 6KB.** Keep concise - show structure and common fields only, not exhaustive spec.

Reference for AI assistants working with Paratext project metadata. Shows what fields exist and how to access them.

---

## Scripture Burrito (metadata.json)

**Format:** JSON → loaded as `dict`
**Spec:** https://docs.burrito.bible/en/latest/

### Common Fields

```python
# Project identification
burrito["identification"]["name"]["en"]           # "Cebuano Popular Version"
burrito["identification"]["abbreviation"]["en"]   # "CPV"

# Language information
burrito["languages"][0]["tag"]                    # "ceb" (ISO 639-3)
burrito["languages"][0]["name"]["en"]             # "Cebuano"
burrito["languages"][0]["name"]["vernacular"]     # "Sinugboanon" (if present)
burrito["languages"][0]["scriptDirection"]        # "ltr" or "rtl"

# Metadata version
burrito["meta"]["version"]                         # "0.3.0"
burrito["meta"]["category"]                        # "source", "target", "derived"

# Type information
burrito["type"]["flavorType"]["name"]             # "scripture"
burrito["type"]["flavorType"]["flavor"]["name"]   # "textTranslation", "audioTranslation"

# Agencies (optional)
burrito["agencies"]                                # list of agency dicts

# Copyright (optional)
burrito["copyright"]["shortStatements"]            # list of copyright statements
```

### Typical Access Pattern

```yaml
- name: load_burrito
  type: function
  function: load_project_file
  inputs:
    base_dir: "${PARATEXT_DIR}"
    project_name: "cebAPDv4"
    file: "metadata.json"
  output:
    - burrito

# Direct dict access in templates
- name: backtranslate
  type: llm
  inputs:
    source_language: "${burrito.languages[0].name.en}"
    iso_code: "${burrito.languages[0].tag}"
    project_name: "${burrito.identification.name.en}"
```

### Notes

- **Multiple languages:** `burrito.languages` is a list; most projects have one item
- **Localized names:** Keys under `name` and `abbreviation` are BCP 47 language tags (e.g., `en`, `fr`, `vernacular`)
- **Optional fields:** Not all projects have `copyright`, `agencies`, or `vernacular` names
- **Prefer Burrito:** If both `metadata.json` and `Settings.xml` exist, prefer Burrito for language info (more structured)

---

## Paratext Settings.xml

**Format:** XML → loaded as `lxml.etree._Element`
**Schema:** Paratext-specific (no public spec)

### Common Elements

```xml
<ScriptureText>
  <LanguageName>Cebuano</LanguageName>
  <LanguageIsoCode>ceb</LanguageIsoCode>
  <FullName>Cebuano Popular Version</FullName>
  <Abbreviation>CPV</Abbreviation>
  <Versification>4</Versification>
  <Encoding>65001</Encoding>
  <Copyright>© 2023 Example Org</Copyright>
  <IsRTL>false</IsRTL>

  <!-- Optional elements -->
  <BiblicalTermsListSetting>Major::BiblicalTerms.xml</BiblicalTermsListSetting>
  <TransliterationFont>Charis SIL</TransliterationFont>
  <BookNameForm>72MAT</BookNameForm>
</ScriptureText>
```

### XPath Queries

```yaml
# Extract language name
xpath_text(settings, ".//LanguageName/text()")          # "Cebuano"

# Extract ISO code
xpath_text(settings, ".//LanguageIsoCode/text()")       # "ceb"

# Extract full project name
xpath_text(settings, ".//FullName/text()")              # "Cebuano Popular Version"

# Extract abbreviation
xpath_text(settings, ".//Abbreviation/text()")          # "CPV"

# Check if RTL
xpath_text(settings, ".//IsRTL/text()")                 # "true" or "false" (string)

# Get versification scheme
xpath_text(settings, ".//Versification/text()")         # "4" (Original versification)

# Get encoding (usually UTF-8)
xpath_text(settings, ".//Encoding/text()")              # "65001" (UTF-8 code page)
```

### Typical Access Pattern

```yaml
- name: load_settings
  type: function
  function: load_project_file
  inputs:
    base_dir: "${PARATEXT_DIR}"
    project_name: "cebAPDv4"
    file: "Settings.xml"
  output:
    - settings

# Extract individual fields
- name: extract_language
  type: function
  function: xpath_text
  inputs:
    element: "${settings}"
    path: ".//LanguageName/text()"
  output:
    - language_name

- name: extract_iso
  type: function
  function: xpath_text
  inputs:
    element: "${settings}"
    path: ".//LanguageIsoCode/text()"
  output:
    - iso_code
```

### Notes

- **Must extract before use:** Cannot pass `_Element` to LLM templates; use `xpath_text()` to extract strings first
- **Optional elements:** Not all projects have `IsRTL`, `TransliterationFont`, or `BiblicalTermsListSetting`
- **Versification codes:** `4` = Original, `1` = English, `2` = Greek, etc. (see Paratext docs)
- **Encoding:** Almost always `65001` (UTF-8)

---

## Other Metadata Files

### BiblicalTerms.xml

Key term renderings for translation consistency.

**Structure (simplified):**
```xml
<BiblicalTermsList>
  <Term Id="אֱלֹהִים">
    <Gloss>God</Gloss>
    <Renderings>
      <Rendering>Dios</Rendering>
    </Renderings>
  </Term>
</BiblicalTermsList>
```

**Note:** Full parsing not yet implemented. Use `load_project_file()` to get Element, then query via XPath.

### BookNames.xml

Localized book names for the project.

**Structure:**
```xml
<BookNames>
  <book code="MAT">
    <long>Mateo</long>
    <short>Mat</short>
    <abbr>Mt</abbr>
  </book>
</BookNames>
```

---

## Choosing Between Burrito and Settings

| Need | Prefer | Reason |
|---|---|---|
| Language name, ISO code | Scripture Burrito | More structured, localized names available |
| Project name, abbreviation | Either | Both have same info |
| Script direction (RTL/LTR) | Scripture Burrito | Explicit `scriptDirection` field |
| Versification | Settings.xml | Burrito doesn't include this |
| Copyright | Either | Both support it |
| Font settings | Settings.xml | Burrito doesn't include UI prefs |

**Best practice:** Load Scripture Burrito if it exists; fall back to Settings.xml if needed.
