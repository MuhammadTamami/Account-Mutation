"""
Find PT Bank Mandiri entry with 27.107.565 Baki Debet
"""
import fitz
import re

filepath = '../test_data/IDEB RIZKY ADE.pdf'

doc = fitz.open(filepath)
full_text = ""
for page in doc:
    full_text += page.get_text() + "\n"
doc.close()

entries = re.split(r'Kredit/Pembiayaan\s+Pelapor', full_text)

print(f"Searching for PT Bank Mandiri with Baki Debet 27.107.565...")

# Search for this specific amount
for i, entry in enumerate(entries[1:], 1):
    if '27.107.565' in entry or '27,107,565' in entry:
        print(f"\n{'='*80}")
        print(f"FOUND at Entry {i}")
        print(f"{'='*80}")
        print(entry[:3000])  # First 3000 chars
        
        # Try to extract key fields
        print(f"\n{'='*80}")
        print(f"Field extraction test:")
        print(f"{'='*80}")
        
        # Baki Debet
        baki_match = re.search(r'Baki Debet[\s\S]{0,200}?Rp\s+([\d.,]+)', entry)
        print(f"Baki Debet: {baki_match.group(1) if baki_match else 'NOT FOUND'}")
        
        # Pelapor - try multiple patterns
        patterns = [
            (r'Tanggal Update\s*\n([^\n]+)', 'Pattern 1: After Tanggal Update'),
            (r'\d+ - ([^\n]+)', 'Pattern 2: After number dash'),
            (r'Cabang\s*\n([^\n]+)', 'Pattern 3: After Cabang'),
            (r'Pelapor\s*\n([^\n]+)', 'Pattern 4: After Pelapor'),
        ]
        
        for pattern, desc in patterns:
            match = re.search(pattern, entry)
            print(f"{desc}: {match.group(1).strip() if match else 'NOT FOUND'}")
        
        # Plafon Awal
        plafon_match = re.search(r'Plafon Awal[\s\S]{0,200}?Rp\s+([\d.,]+)', entry)
        print(f"Plafon Awal: {plafon_match.group(1) if plafon_match else 'NOT FOUND'}")
        
        break

# Also search for other entries that might be missing
print(f"\n\n{'='*80}")
print(f"Checking all entries with Baki > 0 but possibly failing extraction:")
print(f"{'='*80}")

failed_extractions = []

for i, entry in enumerate(entries[1:], 1):
    # Has Baki Debet > 0?
    baki_match = re.search(r'Baki Debet[\s\S]{0,200}?Rp\s+([\d.,]+)', entry)
    if baki_match:
        baki_str = baki_match.group(1)
        baki_val = float(baki_str.replace('.', '').replace(',', '.'))
        
        if baki_val > 0:
            # Try to extract pelapor
            pelapor_match = re.search(r'Tanggal Update\s*\n([^\n]+)', entry)
            if not pelapor_match:
                # This entry has Baki > 0 but failed pelapor extraction
                # Try other patterns
                alt_match = re.search(r'\d+ - ([^\n]+)', entry)
                if alt_match:
                    pelapor = alt_match.group(1).strip()
                else:
                    pelapor = 'FAILED'
                
                if pelapor == 'FAILED' or 'PT Bank Mandiri' in pelapor or 'Mandiri' in pelapor:
                    failed_extractions.append({
                        'entry': i,
                        'pelapor': pelapor,
                        'baki': baki_str
                    })

if failed_extractions:
    print(f"\nFound {len(failed_extractions)} entries with extraction issues:")
    for f in failed_extractions:
        print(f"  Entry {f['entry']}: {f['pelapor']} - Rp {f['baki']}")
else:
    print(f"\nNo failed extractions found with current pattern!")
