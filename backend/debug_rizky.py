"""
Debug IDEB RIZKY ADE.pdf to see why 3 credits are missing
"""
import fitz
import re

filepath = '../test_data/IDEB RIZKY ADE.pdf'

doc = fitz.open(filepath)
print(f"📄 Total pages: {len(doc)}")

# Extract all text
full_text = ""
for page in doc:
    full_text += page.get_text() + "\n"

doc.close()

# Split by "Kredit/Pembiayaan"
entries = re.split(r'Kredit/Pembiayaan\s+Pelapor', full_text)

print(f"\n✓ Total entries found by split: {len(entries)}")
print(f"  (First item is header, so {len(entries)-1} actual entries)")

# Check for entries with Baki Debet > 0
count_with_baki = 0
count_zero_baki = 0
sample_entries = []

for i, entry in enumerate(entries[1:], 1):  # Skip first (header)
    # Extract Baki Debet
    baki_match = re.search(r'Baki Debet\s+Rp\s+([\d.,]+)', entry)
    
    if baki_match:
        baki_str = baki_match.group(1)
        # Convert to float
        baki_str_clean = baki_str.replace('.', '').replace(',', '.')
        try:
            baki_debet = float(baki_str_clean)
            
            if baki_debet > 0:
                count_with_baki += 1
                
                # Store first 5 for debugging
                if len(sample_entries) < 5:
                    # Get pelapor
                    pelapor_match = re.search(r'Tanggal Update\s*\n([^\n]+)', entry)
                    pelapor = pelapor_match.group(1).strip() if pelapor_match else 'Unknown'
                    
                    sample_entries.append({
                        'index': i,
                        'pelapor': pelapor,
                        'baki_debet': f"Rp {baki_str}"
                    })
            else:
                count_zero_baki += 1
        except:
            print(f"⚠ Entry {i}: Could not parse Baki Debet: {baki_str}")
    else:
        print(f"⚠ Entry {i}: No Baki Debet found")

print(f"\n📊 Results:")
print(f"  - Entries with Baki Debet > 0: {count_with_baki}")
print(f"  - Entries with Baki Debet = 0: {count_zero_baki}")
print(f"  - Total: {count_with_baki + count_zero_baki}")

print(f"\n📋 Sample entries with Baki Debet > 0:")
for s in sample_entries:
    print(f"  {s['index']}. {s['pelapor']} - {s['baki_debet']}")

# Now let's check if the split pattern is correct
print(f"\n🔍 Checking split pattern variations:")
alt_patterns = [
    r'Kredit/Pembiayaan',
    r'Kredit/Pembiayaan\s+Pelapor',
    r'Kredit/Pembiayaan\nPelapor',
]

for pattern in alt_patterns:
    matches = re.findall(pattern, full_text)
    print(f"  Pattern '{pattern}': {len(matches)} matches")
