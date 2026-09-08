"""Test Hanisa BRI file for monthly fee detection"""
import sys
sys.path.insert(0, 'processors')

from bri_processor import process_bri_file
import pandas as pd

pdf_path = r'uploads\HANISA JANUARI.pdf'

print("=" * 80)
print("Hanisa BRI File - Monthly Fee Detection")
print("=" * 80)

df = process_bri_file(pdf_path, 'pdf')

print(f"\nResults:")
print(f"  Total transactions: {len(df)}")
print(f"  Debit: {len(df[df['Type'] == 'Debit'])}")
print(f"  Credit: {len(df[df['Type'] == 'Credit'])}")

# Check for monthly fee specifically
print(f"\n{'='*80}")
print("Looking for 'monthly' keyword:")
print('='*80)

monthly_found = False
for idx, row in df.iterrows():
    if 'monthly' in row['Description'].lower():
        print(f"FOUND: {row['Date']} | {row['Type']:6} | {row['Amount']:>15} | {row['Description']}")
        monthly_found = True

if not monthly_found:
    print("  No 'monthly' keyword found in extracted transactions")

# Check for 'fee' keyword
print(f"\n{'='*80}")
print("Looking for 'fee' keyword:")
print('='*80)

fee_found = False
for idx, row in df.iterrows():
    if 'fee' in row['Description'].lower():
        print(f"FOUND: {row['Date']} | {row['Type']:6} | {row['Amount']:>15} | {row['Description']}")
        fee_found = True

if not fee_found:
    print("  No 'fee' keyword found in extracted transactions")

# Check raw PDF for monthly fee
print(f"\n{'='*80}")
print("Checking RAW PDF for 'monthly' text:")
print('='*80)

import pdfplumber
with pdfplumber.open(pdf_path) as pdf:
    monthly_in_pdf = False
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'monthly' in line.lower() or 'biaya bulanan' in line.lower():
                    print(f"\n[Page {page_num + 1}, Line {i + 1}]")
                    print(f"  Current: {line}")
                    if i > 0:
                        print(f"  Before:  {lines[i-1]}")
                    if i < len(lines) - 1:
                        print(f"  After:   {lines[i+1]}")
                    if i < len(lines) - 2:
                        print(f"  After+2: {lines[i+2]}")
                    monthly_in_pdf = True
    
    if not monthly_in_pdf:
        print("  No 'monthly' text found in PDF")

# Show all transactions with small amounts (likely fees)
print(f"\n{'='*80}")
print("Small amount transactions (< 100,000) - likely fees:")
print('='*80)

small_transactions = df[df['Amount'].apply(lambda x: float(str(x).replace(',', '')) < 100000)]
for idx, row in small_transactions.head(20).iterrows():
    print(f"{row['Date']} | {row['Type']:6} | {row['Amount']:>15} | {row['Description'][:60]}")

print(f"\nTotal small transactions: {len(small_transactions)}")
