"""Debug BCA April 2026 PDF structure"""
import fitz
import re

filepath = '../test_data/9. April 2026.pdf'

doc = fitz.open(filepath)

print("=" * 80)
print("BCA April 2026 - PDF Structure Analysis")
print("=" * 80)

# Check first page for summary
print("\nFIRST PAGE (Summary):")
print("=" * 80)
first_text = doc[0].get_text()
lines = first_text.split('\n')

for i, line in enumerate(lines[:50]):  # First 50 lines
    if 'MUTASI' in line or 'SALDO' in line or line.strip().replace(',', '').replace('.', '').isdigit():
        print(f"{i:3d}: {line}")

# Check a middle page for transaction format
print("\n" + "=" * 80)
print("SAMPLE PAGE (Page 10) - Transaction Format:")
print("=" * 80)

page10 = doc[9]  # 0-indexed
text10 = page10.get_text()
lines10 = text10.split('\n')

print(f"Total lines: {len(lines10)}")
print("\nFirst 80 lines:")
for i, line in enumerate(lines10[:80]):
    print(f"{i:3d}: {line}")

# Look for patterns
print("\n" + "=" * 80)
print("Pattern Analysis:")
print("=" * 80)

dates = [l for l in lines10 if re.match(r'^\d{2}/\d{2}$', l)]
print(f"Date lines (DD/MM): {len(dates)}")

db_cr = [l for l in lines10 if l.strip() in ['DB', 'CR', 'D', 'C']]
print(f"DB/CR indicator lines: {len(db_cr)}")

# Look for amount pattern
amounts = [l for l in lines10 if re.search(r'[\d,]+\.\d{2}', l)]
print(f"Lines with amounts: {len(amounts)}")
if amounts:
    print("\nFirst 10 amount lines:")
    for line in amounts[:10]:
        print(f"  {line}")

doc.close()
