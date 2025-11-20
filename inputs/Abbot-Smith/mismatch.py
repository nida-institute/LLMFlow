import unicodedata
from lxml import etree
import csv

def normalize_greek(text):
    """Normalize Greek text to NFC for comparison"""
    return unicodedata.normalize('NFC', text.lower().strip())

# Parse Abbott-Smith
tree = etree.parse('abbott-smith.tei.xml')
root = tree.getroot()

# Check for namespace
print(f"Root tag: {root.tag}")
print(f"Root namespace: {root.nsmap}")

# Define namespace if present
ns = root.nsmap.copy()
if None in ns:
    ns['tei'] = ns.pop(None)  # Give default namespace a prefix

print(f"\nNamespaces: {ns}")

# Check the actual structure first
print("\nChecking XML structure...")
if 'tei' in ns:
    entries = tree.xpath('//tei:entry', namespaces=ns)
else:
    entries = tree.xpath('//entry')

print(f"Found {len(entries)} entry elements")

if entries:
    first_entry = entries[0]
    print(f"\nFirst entry structure:")
    print(etree.tostring(first_entry, encoding='unicode', pretty_print=True)[:500])

# Build Abbott-Smith index
abbott_entries = {}
for entry in entries:
    # Get xml:id directly from entry
    xml_id = entry.get('{http://www.w3.org/XML/1998/namespace}id')

    # Try multiple ways to get the lemma form
    if 'tei' in ns:
        form_elem = entry.find('.//tei:form[@type="lemma"]', namespaces=ns)
        if form_elem is None:
            form_elem = entry.find('.//tei:form', namespaces=ns)
        strong_elem = entry.find('.//tei:number[@type="strongs"]', namespaces=ns)
    else:
        form_elem = entry.find('.//form[@type="lemma"]')
        if form_elem is None:
            form_elem = entry.find('.//form')
        strong_elem = entry.find('.//number[@type="strongs"]')

    if xml_id:
        lemma_text = form_elem.text if form_elem is not None and form_elem.text else xml_id
        strongs = strong_elem.text if strong_elem is not None else None

        lemma_normalized = normalize_greek(lemma_text)
        original_lemma = unicodedata.normalize('NFC', lemma_text)

        abbott_entries[lemma_normalized] = {
            'xml_id': xml_id,
            'strongs': strongs,
            'original_lemma': original_lemma
        }

print(f"\nBuilt index with {len(abbott_entries)} Abbott-Smith entries")
print(f"Sample entries: {list(abbott_entries.keys())[:5]}")

# Read status.tsv
macula_lemmas = {}
with open('status.tsv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        lemma = normalize_greek(row['lemma'])
        original = unicodedata.normalize('NFC', row['lemma'])
        macula_lemmas[lemma] = {**row, 'original_lemma': original}

print(f"Read {len(macula_lemmas)} Macula lemmas")
print(f"Sample lemmas: {list(macula_lemmas.keys())[:5]}")

# Create mapping
mapping = {}
for macula_norm, macula_data in macula_lemmas.items():
    original_lemma = macula_data['original_lemma']
    if macula_norm in abbott_entries:
        mapping[original_lemma] = {
            'abbott_lemma': abbott_entries[macula_norm]['original_lemma'],
            'abbott_xml_id': abbott_entries[macula_norm]['xml_id'],
            'strongs': abbott_entries[macula_norm]['strongs'],
            'matched': True
        }
    else:
        mapping[original_lemma] = {
            'abbott_lemma': None,
            'abbott_xml_id': None,
            'strongs': None,
            'matched': False
        }

# Report mismatches
matched = [k for k, v in mapping.items() if v['matched']]
unmatched = [k for k, v in mapping.items() if not v['matched']]

print(f"\n✓ Matched entries: {len(matched)}")
print(f"✗ Unmatched entries: {len(unmatched)}")

if matched:
    print(f"\nFirst 10 matched:")
    for lemma in matched[:10]:
        data = mapping[lemma]
        print(f"  {lemma} -> {data['abbott_xml_id']} (Strong's: {data['strongs']})")

if unmatched:
    print(f"\nFirst 10 unmatched:")
    for lemma in unmatched[:10]:
        print(f"  {lemma}")

# Write mapping to TSV in NFC
with open('lemma_mapping.tsv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerow(['macula_lemma', 'abbott_lemma', 'abbott_xml_id', 'strongs', 'matched'])

    for macula_lemma, data in sorted(mapping.items()):
        row = [
            unicodedata.normalize('NFC', macula_lemma),
            unicodedata.normalize('NFC', data['abbott_lemma']) if data['abbott_lemma'] else '',
            data['abbott_xml_id'] or '',
            data['strongs'] or '',
            str(data['matched'])
        ]
        writer.writerow(row)

print(f"\nCreated lemma_mapping.tsv with {len(mapping)} entries")

