"""
Debug IDEB RIZKY ADE.pdf - Find the 3 missing credits
Check which entries have Baki Debet > 0 but failed to extract
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

# Check each entry for Baki Debet
credits_with_baki = []
credits_failed = []

for i, entry in enumerate(entries[1:], 1):  # Skip first (header)
    # Try both patterns
    baki_match = re.search(r'Baki Debet\s+Rp\s+([\d.,]+)', entry)
    if not baki_match:
        baki_match = re.search(r'Baki Debet[\s\S]{0,200}?Rp\s+([\d.,]+)', entry)
    
    if baki_match:
        baki_str = baki_match.group(1)
        # Convert to float
        baki_str_clean = baki_str.replace('.', '').replace(',', '.')
        try:
            baki_debet = float(baki_str_clean)
            
            if baki_debet > 0:
                # Try to extract pelapor
                pelapor_match = re.search(r'Tanggal Update\s*\n([^\n]+)', entry)
                if not pelapor_match:
                    # Try alternate pattern: after numbers like "451 - "
                    pelapor_match = re.search(r'\d+ - ([^\n]+)', entry)
                
                pelapor = pelapor_match.group(1).strip() if pelapor_match else '???'
                
                # Try to extract Plafon Awal
                plafon_match = re.search(r'Plafon Awal\s+Rp\s+([\d.,]+)', entry)
                if not plafon_match:
                    plafon_match = re.search(r'Plafon Awal[\s\S]{0,200}?Rp\s+([\d.,]+)', entry)
                
                plafon = plafon_match.group(1) if plafon_match else 'N/A'
                
                # Check if extraction would work
                if not pelapor_match:
                    credits_failed.append({
                        'entry': i,
                        'pelapor': pelapor,
                        'baki': baki_str,
                        'plafon': plafon,
                        'reason': 'No Pelapor match'
                    })
                elif not plafon_match:
                    credits_failed.append({
                        'entry': i,
                        'pelapor': pelapor,
                        'baki': baki_str,
                        'plafon': plafon,
                        'reason': 'No Plafon match'
                    })
                else:
                    credits_with_baki.append({
                        'entry': i,
                        'pelapor': pelapor,
                        'baki': baki_str,
                        'plafon': plafon
                    })
        except:
            pass

print(f"\n📊 Results:")
print(f"  Credits successfully extracted: {len(credits_with_baki)}")
print(f"  Credits with Baki > 0 but FAILED extraction: {len(credits_failed)}")

if credits_failed:
    print(f"\n❌ Failed Extractions:")
    for c in credits_failed:
        print(f"  Entry {c['entry']}: {c['pelapor']}")
        print(f"    Baki Debet: Rp {c['baki']}")
        print(f"    Plafon: {c['plafon']}")
        print(f"    Reason: {c['reason']}")
        print()

# Show specific entries that might be problematic
print(f"\n🔍 Checking specific entries mentioned by user:")
print(f"  Looking for 27 juta (27,000,000) entries...")

count_27m = 0
for i, entry in enumerate(entries[1:], 1):
    if '27.000.000' in entry or '27,000,000' in entry:
        # Check Baki Debet
        baki_match = re.search(r'Baki Debet[\s\S]{0,200}?Rp\s+([\d.,]+)', entry)
        if baki_match:
            baki_str = baki_match.group(1)
            baki_clean = baki_str.replace('.', '').replace(',', '.')
            try:
                baki = float(baki_clean)
                if baki > 0:
                    count_27m += 1
                    print(f"  Entry {i}: Baki Debet = Rp {baki_str}")
            except:
                pass

print(f"  Total entries with ~27 juta and Baki > 0: {count_27m}")
