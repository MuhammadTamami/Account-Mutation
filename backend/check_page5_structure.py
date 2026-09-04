"""Check page 5 structure in detail"""
import pdfplumber

filepath = '../test_data/acct_1977_Maret 2026.pdf'
pdf = pdfplumber.open(filepath, password='07031985')

page5 = pdf.pages[4]  # 0-indexed
text5 = page5.extract_text()
lines5 = text5.split('\n')

print("=" * 80)
print("PAGE 5 - Complete Line-by-Line Analysis")
print("=" * 80)

for i, line in enumerate(lines5):
    print(f"{i:3d}: {line}")

pdf.close()

print("\n" + "=" * 80)
print("STRUCTURE ANALYSIS")
print("=" * 80)
print("""
Line 0: Account Statement (header)
Line 1: Created 30 Jun 2026 10:56:41 (header)
Line 2: 00 Bunga 03101 - 0.00 159,475.25 295,162,850.73  ← CREDIT (amounts)
Line 3: 31/03/2026 23:59:                                  ← Date for BOTH transactions!
Line 4: Pajak 03101 - 31,895.05 0.00 295,130,955.68       ← DEBIT (amounts)
Line 5: 00 (row number?)
Line 6: For further questions... (footer)

PATTERN FOUND:
Multiple transactions share the SAME date line!
- Line 2 (Bunga - credit) uses date from Line 3
- Line 4 (Pajak - debit) ALSO uses date from Line 3

Current fix only handles ONE transaction before the date.
Need to check AFTER the date too!
""")
