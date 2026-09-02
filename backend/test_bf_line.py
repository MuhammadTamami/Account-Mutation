# -*- coding: utf-8 -*-
"""
Test B/F (Brought Forward) line parsing
"""
import pdfplumber

filepath = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\RK GIRO PTBDK.pdf'

pdf = pdfplumber.open(filepath)
page = pdf.pages[0]
text = page.extract_text()
lines = text.split('\n')

print("Looking for B/F and first transactions:\n")
print("=" * 80)

for i, line in enumerate(lines[9:15], 9):
    print(f"{i+1:3d}: {line}")

print("=" * 80)

# Parse B/F line
bf_line = "B/F 1,046,350.86 Cr"
print(f"\nTesting B/F line: {bf_line}")

import re
# B/F pattern: "B/F <balance> Cr/Dr"
bf_match = re.match(r'^B/F\s+([\d,\.]+)\s+(Cr|Dr)$', bf_line.strip())
if bf_match:
    balance_str = bf_match.group(1)
    balance_type = bf_match.group(2)
    print(f"  Matched!")
    print(f"  Balance: {balance_str}")
    print(f"  Type: {balance_type}")
else:
    print(f"  Not matched")

pdf.close()
