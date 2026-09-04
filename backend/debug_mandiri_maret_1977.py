"""Debug Mandiri Maret 1977 - check why missing 1 credit"""
import pdfplumber
import re
import pandas as pd

filepath = '../test_data/acct_1977_Maret 2026.pdf'

# Open PDF
pdf = pdfplumber.open(filepath, password='07031985')

print(f"Total pages: {len(pdf.pages)}")
print("=" * 80)

# Check each page
for page_num, page in enumerate(pdf.pages):
    print(f"\nPAGE {page_num + 1}")
    print("=" * 80)
    
    text = page.extract_text()
    
    if not text:
        print("❌ No text extracted")
        continue
    
    lines = text.split('\n')
    
    # Count potential transactions
    # Format 1: DD/MM/YYYY HH:MM:SS
    format1_dates = [l for l in lines if re.match(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}', l)]
    
    # Format 2: DD Mon YYYY,
    format2_dates = [l for l in lines if re.match(r'\d{2}\s+[A-Za-z]{3}\s+\d{4},', l)]
    
    # Format 3: DD Mon YYYY (no comma)
    format3_dates = [l for l in lines if re.search(r'\d{2}\s+[A-Za-z]{3}\s+\d{4}(?!,)', l) and 'No Date' not in l]
    
    print(f"Format 1 (DD/MM/YYYY HH:MM): {len(format1_dates)} dates")
    print(f"Format 2 (DD Mon YYYY,): {len(format2_dates)} dates")
    print(f"Format 3 (DD Mon YYYY): {len(format3_dates)} dates")
    
    # Show first 30 lines
    print(f"\nFirst 30 lines:")
    for i, line in enumerate(lines[:30]):
        print(f"  {i:3d}: {line}")
    
    # Show last 30 lines
    print(f"\nLast 30 lines:")
    for i, line in enumerate(lines[-30:]):
        actual_line_num = len(lines) - 30 + i
        print(f"  {actual_line_num:3d}: {line}")
    
    # Look for credit transactions (+ sign or 0.00 in debit column)
    credit_indicators = [l for l in lines if '+' in l or re.search(r'0\.00\s+[\d,]+\.[\d]{2}\s+[\d,]+\.[\d]{2}', l)]
    print(f"\nPotential credits on this page: {len(credit_indicators)}")
    if credit_indicators:
        for line in credit_indicators[:5]:
            print(f"  > {line}")

pdf.close()

print("\n" + "=" * 80)
print("Now running actual processor...")
print("=" * 80)

from processors.mandiri_processor import process_mandiri_pdf

df = process_mandiri_pdf(filepath)

print(f"\nResults:")
print(f"Total records: {len(df)}")
print(f"Credit: {len(df[df['Type'] == 'Credit'])}")
print(f"Debit: {len(df[df['Type'] == 'Debit'])}")

# Show all credits
print(f"\nAll {len(df[df['Type'] == 'Credit'])} Credit transactions:")
credits = df[df['Type'] == 'Credit'].sort_values('Date')
for idx, row in credits.iterrows():
    print(f"  {row['Date'].strftime('%d/%m/%Y')}: {row['Description'][:50]:50s} Rp {row['Amount']}")
