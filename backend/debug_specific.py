"""
Find the specific 27 million credit that's missing
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

print(f"Searching for entries with Plafon around 27 million...")

found_27m = []

for i, entry in enumerate(entries[1:], 1):
    # Search for Plafon Awal with 27 million
    plafon_matches = re.findall(r'Plafon Awal[\s\S]{0,50}?Rp\s+([\d.,]+)', entry)
    
    for plafon_str in plafon_matches:
        # Check if it's around 27 million
        plafon_clean = plafon_str.replace('.', '').replace(',', '.')
        try:
            plafon_val = float(plafon_clean)
            if 26000000 < plafon_val < 28000000:  # Between 26-28 million
                # Get Baki Debet
                baki_match = re.search(r'Baki Debet[\s\S]{0,200}?Rp\s+([\d.,]+)', entry)
                baki_str = baki_match.group(1) if baki_match else 'NOT FOUND'
                baki_clean = baki_str.replace('.', '').replace(',', '.')
                try:
                    baki_val = float(baki_clean)
                except:
                    baki_val = 0
                
                # Get Pelapor
                pelapor_match = re.search(r'Tanggal Update\s*\n([^\n]+)', entry)
                if not pelapor_match:
                    pelapor_match = re.search(r'\d+ - ([^\n]+)', entry)
                pelapor = pelapor_match.group(1).strip() if pelapor_match else 'NOT FOUND'
                
                found_27m.append({
                    'entry': i,
                    'pelapor': pelapor,
                    'plafon': plafon_str,
                    'baki_debet': baki_str,
                    'baki_val': baki_val
                })
        except:
            pass

print(f"\nFound {len(found_27m)} entries with Plafon ~27 million:")
for f in found_27m:
    print(f"\nEntry {f['entry']}:")
    print(f"  Pelapor: {f['pelapor']}")
    print(f"  Plafon Awal: Rp {f['plafon']}")
    print(f"  Baki Debet: Rp {f['baki_debet']}")
    print(f"  Baki > 0: {f['baki_val'] > 0}")
    
# Also check total entries with Baki > 0
print(f"\n{'='*80}")
print(f"Total count verification:")

count_baki_positive = 0
for i, entry in enumerate(entries[1:], 1):
    baki_match = re.search(r'Baki Debet[\s\S]{0,200}?Rp\s+([\d.,]+)', entry)
    if baki_match:
        baki_str = baki_match.group(1)
        baki_clean = baki_str.replace('.', '').replace(',', '.')
        try:
            baki_val = float(baki_clean)
            if baki_val > 0:
                count_baki_positive += 1
        except:
            pass

print(f"Total entries with Baki Debet > 0: {count_baki_positive}")
print(f"Processor extracted: 70")
print(f"Missing: {count_baki_positive - 70}")
