# Versification Services using Copenhagen Alliance Standards

## Problem Statement

Biblical translations often use different versification systems:
- **Hebrew vs Greek OT:** Verse numbering differs (e.g., Psalm headings)
- **Protestant vs Catholic:** Different books and chapter divisions
- **Septuagint (LXX):** Different organization and numbering
- **Modern translations:** Sometimes follow different traditions

**Without versification services, LLMFlow cannot:**
- Map references between different Bible versions
- Align parallel texts for comparison
- Handle cross-references correctly
- Support multilingual biblical scholarship
- Work with non-English versification traditions

## Copenhagen Alliance Standard

The **Copenhagen Alliance for Open Biblical Language Resources** provides:
- Standardized versification mappings
- Machine-readable data formats
- Open-source reference implementations
- Support for major versification traditions

**Resources:**
- GitHub: https://github.com/Copenhagen-Alliance
- Versification spec: https://github.com/Copenhagen-Alliance/versification-specification
- Reference data: https://github.com/Copenhagen-Alliance/versification-data

## Use Cases in LLMFlow

### 1. **Reference Normalization**
```yaml
# Pipeline needs to work with both LXX and MT references
input: "Psalm 13:1 (LXX)"  # → "Psalm 14:1 (MT)"
```

### 2. **Cross-Version Alignment**
```yaml
# Leader's guide references ESV, user has NIV
- Align passages between versification systems
- Map study notes to correct verses
```

### 3. **Hebrew Bible Support**
```yaml
# Hebrew verse numbering differs from English
- Genesis 31:55 (Hebrew) = Genesis 32:1 (English)
- Proper mapping required for Hebrew-English workflows
```

### 4. **Deuterocanonical Books**
```yaml
# Catholic Bibles have different book ordering
- Tobit, Judith, Wisdom, Sirach, Baruch, 1-2 Maccabees
- Additions to Daniel and Esther
```

### 5. **Scholarly Work**
```yaml
# Academic pipelines need multiple traditions
- Septuagint (LXX) numbering
- Masoretic Text (MT) numbering
- Vulgate numbering
- Dead Sea Scrolls references
```

## Proposed Implementation

### Phase 1: Data Integration
```python
# Add Copenhagen Alliance versification data as package resource
from llmflow.versification import VersificationSystem

# Load standard versification schemes
mt = VersificationSystem.load('masoretic')
lxx = VersificationSystem.load('septuagint')
vulgate = VersificationSystem.load('vulgate')
protestant = VersificationSystem.load('protestant')
catholic = VersificationSystem.load('catholic')
```

### Phase 2: Reference Mapping
```python
# Map references between systems
from llmflow.versification import map_reference

ref = parse_reference("Psalm 13:1", system='lxx')
mapped = map_reference(ref, from_system='lxx', to_system='mt')
# Result: "Psalm 14:1"
```

### Phase 3: YAML Integration
```yaml
# Pipeline can specify versification system
vars:
  versification: masoretic  # or lxx, vulgate, protestant, catholic

steps:
  - name: normalize_references
    uses: versification
    inputs:
      text: ${input_passage}
      from_system: ${source_versification}
      to_system: ${versification}
```

### Phase 4: Alignment Services
```python
# Align passages across versification systems
from llmflow.versification import align_passages

alignment = align_passages(
    passage1="Genesis 1:1-31",
    system1='mt',
    passage2="Genesis 1:1-31",
    system2='lxx'
)

# Returns verse-by-verse mapping with differences
```

## Copenhagen Alliance Integration

### Required Data Files
```
src/llmflow/data/versification/
  ├── protestant.json       # Protestant tradition
  ├── catholic.json         # Catholic tradition
  ├── orthodox.json         # Eastern Orthodox
  ├── masoretic.json        # Hebrew Bible (MT)
  ├── septuagint.json       # Greek OT (LXX)
  ├── vulgate.json          # Latin Vulgate
  └── mappings/
      ├── lxx-to-mt.json
      ├── mt-to-protestant.json
      └── ...
```

### API Design
```python
class VersificationSystem:
    def __init__(self, name: str, data: dict):
        self.name = name
        self.books = ...  # Book list and metadata
        self.chapters = ...  # Chapter divisions
        self.verses = ...  # Verse counts

    @classmethod
    def load(cls, system_name: str) -> 'VersificationSystem':
        """Load a standard versification system."""
        ...

    def normalize_reference(self, ref: str) -> BibleReference:
        """Parse and normalize a reference in this system."""
        ...

    def has_book(self, book: str) -> bool:
        """Check if this system includes a book."""
        ...

    def verse_count(self, book: str, chapter: int) -> int:
        """Get verse count for a chapter."""
        ...

def map_reference(
    ref: BibleReference,
    from_system: str,
    to_system: str
) -> Optional[BibleReference]:
    """Map a reference between versification systems."""
    ...

def align_passages(
    passage1: str,
    system1: str,
    passage2: str,
    system2: str
) -> AlignmentResult:
    """Align two passages with different versification."""
    ...
```

## Example Workflows

### Hebrew-English Study Guide
```yaml
# Generate study guide aligned for both Hebrew and English readers
pipeline:
  - name: load_hebrew_text
    inputs:
      passage: "Genesis 31:55"
      versification: masoretic

  - name: map_to_english
    uses: versification
    inputs:
      reference: ${passage}
      from_system: masoretic
      to_system: protestant
    # Output: "Genesis 32:1"

  - name: generate_study_notes
    inputs:
      hebrew_ref: ${passage}
      english_ref: ${mapped_reference}
```

### Cross-Translation Alignment
```yaml
# Align study materials for multiple Bible versions
pipeline:
  - name: align_references
    uses: versification
    inputs:
      base_text: ${esv_text}
      base_system: protestant
      target_systems:
        - catholic
        - orthodox
        - lxx
```

## Data Format (Copenhagen Alliance JSON)

```json
{
  "versification": "protestant",
  "version": "1.0",
  "books": [
    {
      "id": "GEN",
      "name": "Genesis",
      "testament": "OT",
      "chapters": [
        {"chapter": 1, "verses": 31},
        {"chapter": 2, "verses": 25},
        ...
      ]
    }
  ],
  "mappings": {
    "from": "lxx",
    "rules": [
      {
        "from": "Psalm 13:1",
        "to": "Psalm 14:1",
        "note": "LXX Psalm numbering differs from MT"
      }
    ]
  }
}
```

## Testing Strategy

```python
# test_versification.py
def test_load_system():
    mt = VersificationSystem.load('masoretic')
    assert mt.verse_count('Genesis', 1) == 31

def test_map_psalm_lxx_to_mt():
    ref = parse_reference("Psalm 13:1", system='lxx')
    mapped = map_reference(ref, from_system='lxx', to_system='mt')
    assert str(mapped) == "Psalm 14:1"

def test_deuterocanonical_books():
    catholic = VersificationSystem.load('catholic')
    protestant = VersificationSystem.load('protestant')

    assert catholic.has_book('Tobit')
    assert not protestant.has_book('Tobit')
```

## Dependencies

- **Copenhagen Alliance data:** MIT/CC0 licensed, can bundle
- **Python stdlib only:** No new external dependencies needed
- **Integration with existing:** Works with `llmflow.utils.data.parse_bible_reference()`

## Benefits

1. **Scholarly Accuracy:** Handle Hebrew/Greek versification correctly
2. **Multilingual Support:** Work with any Bible tradition
3. **Cross-Reference Validation:** Verify references are valid per system
4. **Translation Alignment:** Map study materials across versions
5. **Standards Compliance:** Use industry-standard Copenhagen Alliance data

## Implementation Checklist

- [ ] Download Copenhagen Alliance versification data
- [ ] Create `llmflow/versification/` module
- [ ] Implement `VersificationSystem` class
- [ ] Implement `map_reference()` function
- [ ] Implement `align_passages()` function
- [ ] Add YAML pipeline support (`uses: versification`)
- [ ] Write comprehensive tests
- [ ] Document versification workflows
- [ ] Add examples for common use cases
- [ ] Integrate with existing reference parsing

## Timeline Estimate

- **Phase 1 (Data Integration):** 2-3 days
- **Phase 2 (Reference Mapping):** 3-4 days
- **Phase 3 (YAML Integration):** 2-3 days
- **Phase 4 (Alignment):** 4-5 days
- **Testing & Documentation:** 3-4 days

**Total:** 2-3 weeks

## Questions to Decide

1. **Which systems to support initially?**
   Recommendation: Protestant, Catholic, Masoretic, LXX (most common)

2. **Bundle data or download on demand?**
   Recommendation: **Bundle** - versification data is small (~1-2MB)

3. **API stability?**
   Recommendation: Mark as **experimental** initially, stabilize after user feedback

## Acceptance Criteria

- [ ] Can load 4+ versification systems
- [ ] Can map Psalm references LXX ↔ MT correctly
- [

] Deuterocanonical books handled correctly
- [ ] YAML `uses: versification` works in pipelines
- [ ] Comprehensive test coverage (>85%)
- [ ] Documentation with examples
- [ ] No new external dependencies

## References

- Copenhagen Alliance: https://github.com/Copenhagen-Alliance
- Versification Spec: https://github.com/Copenhagen-Alliance/versification-specification
- USFM Standard: https://ubsicap.github.io/usfm/
- Bible versification systems: https://en.wikipedia.org/wiki/Chapters_and_verses_of_the_Bible
