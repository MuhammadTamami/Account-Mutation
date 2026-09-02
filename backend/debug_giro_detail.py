# -*- coding: utf-8 -*-
"""
Debug RK GIRO PTBDK to see exact text extraction
"""
import pdfplumber

filepath = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\RK GIRO PTBDK.pdf'

print("Extracting text from RK GIRO PTBDK.pdf...")
print("=" * 80)

pdf = pdfplumber.open(filepath)
print(f"Total pages: {len(pdf.pages)}\n")

# Show first page in detail
page = pdf.pages[0]
text = page.extract_text()

lines = text.split('\n')
print(f"Page 1 - Total lines: {len(lines)}\n")
print("First 40 lines:")
print("-" * 80)

for i, line in enumerate(lines[:40], 1):
    print(f"{i:3d}: {line}")

print("-" * 80)

# Focus on January transactions
print("\nLooking for January transactions (lines 11-20):")
print("-" * 80)
for i in range(10, min(20, len(lines))):
    print(f"{i+1:3d}: {lines[i]}")

pdf.close()
