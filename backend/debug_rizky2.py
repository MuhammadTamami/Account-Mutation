"""
Debug IDEB RIZKY ADE.pdf - Check actual text format
"""
import fitz
import re

filepath = '../test_data/IDEB RIZKY ADE.pdf'

doc = fitz.open(filepath)

# Extract all text
full_text = ""
for page in doc:
    full_text += page.get_text() + "\n"

doc.close()

# Split by pattern
entries = re.split(r'Kredit/Pembiayaan\s+Pelapor', full_text)

print(f"Total entries: {len(entries)-1}")

# Show first entry in detail
if len(entries) > 1:
    print(f"\n{'='*80}")
    print(f"ENTRY 1 (first 2000 characters):")
    print(f"{'='*80}")
    print(entries[1][:2000])
    
    print(f"\n{'='*80}")
    print(f"ENTRY 2 (first 2000 characters):")
    print(f"{'='*80}")
    print(entries[2][:2000] if len(entries) > 2 else "N/A")

# Search for various "Baki" patterns
print(f"\n{'='*80}")
print(f"Searching for 'Baki' variations:")
print(f"{'='*80}")

baki_patterns = [
    r'Baki Debet',
    r'Baki\s+Debet',
    r'Baki\nDebet',
    r'BakiDebet',
    r'(?i)baki.*debet',
]

for pattern in baki_patterns:
    matches = re.findall(pattern, full_text[:10000])  # First 10000 chars
    print(f"  Pattern '{pattern}': {len(matches)} matches")
    if matches:
        print(f"    Sample: {matches[0]}")

# Check if text contains common IDEB keywords
keywords = ['Plafon Awal', 'Suku Bunga', 'Tanggal Mulai', 'Tanggal Jatuh Tempo', 'Kualitas']
print(f"\n{'='*80}")
print(f"Checking for IDEB keywords:")
print(f"{'='*80}")
for kw in keywords:
    count = full_text.count(kw)
    print(f"  '{kw}': {count} occurrences")
