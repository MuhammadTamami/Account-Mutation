import fitz
import re

doc = fitz.open('../test_data/IDEB PUTRI MAYA.pdf')

# Extract all text
full_text = ""
for page in doc:
    full_text += page.get_text() + "\n"

doc.close()

# Split into credit entries
entries = re.split(r'Kredit/Pembiayaan\s+Pelapor', full_text)

print(f"Found {len(entries)} entries\n")

# Show first entry with Baki Debet > 0
for i, entry in enumerate(entries[1:4]):  # Check first 3 entries
    print(f"=== Entry {i+1} - First 500 chars ===")
    print(entry[:500])
    print("\n" + "="*80 + "\n")
