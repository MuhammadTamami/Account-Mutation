"""Find the missing debit transaction in Mandiri March 1977"""
import pdfplumber
import re
import pandas as pd
from processors.mandiri_processor import process_mandiri_pdf, clean_amount

filepath = '../test_data/acct_1977_Maret 2026.pdf'

# Get extracted transactions
df = process_mandiri_pdf(filepath)

print("=" * 80)
print("ANALYSIS: Finding Missing Debit Transaction")
print("=" * 80)

# Summary
summary = df.attrs.get('pdf_summary', {})
expected_debit = summary.get('no_of_debit', 0)
expected_credit = summary.get('no_of_credit', 0)
actual_debit = len(df[df['Type'] == 'Debit'])
actual_credit = len(df[df['Type'] == 'Credit'])

print(f"\nExpected: Debit={expected_debit}, Credit={expected_credit}")
print(f"Actual:   Debit={actual_debit}, Credit={actual_credit}")
print(f"\nMissing: {expected_debit - actual_debit} debit transaction(s)")

# Now manually parse ALL lines to find potential debits
pdf = pdfplumber.open(filepath, password='07031985')

all_potential_debits = []

for page_num, page in enumerate(pdf.pages):
    text = page.extract_text()
    if not text:
        continue
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        # Look for lines with 3 numbers pattern (debit credit balance)
        numbers = re.findall(r'[\d,]+\.[\d]{2}', line)
        
        if len(numbers) >= 3:
            debit_str = numbers[-3]
            credit_str = numbers[-2]
            balance_str = numbers[-1]
            
            debit = clean_amount(debit_str)
            credit = clean_amount(credit_str)
            balance = clean_amount(balance_str)
            
            # This is a debit if debit > 0 and credit == 0
            if debit > 0 and credit == 0:
                # Try to find date nearby
                date_found = None
                desc = line
                
                # Check previous 3 lines for date
                for j in range(max(0, i-3), i):
                    prev_line = lines[j]
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', prev_line)
                    if date_match:
                        date_found = date_match.group(1)
                        break
                
                # Check next 3 lines for date
                if not date_found:
                    for j in range(i+1, min(len(lines), i+4)):
                        next_line = lines[j]
                        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', next_line)
                        if date_match:
                            date_found = date_match.group(1)
                            break
                
                all_potential_debits.append({
                    'page': page_num + 1,
                    'line_num': i,
                    'date': date_found or '?',
                    'debit': debit,
                    'balance': balance,
                    'desc': desc[:60]
                })

pdf.close()

print(f"\n📊 Found {len(all_potential_debits)} potential debit lines in PDF")

# Now check which ones are NOT in our extracted data
print("\n🔍 Checking which debits are missing...")

extracted_debits = df[df['Type'] == 'Debit']

missing_debits = []

for pot in all_potential_debits:
    # Check if this debit amount exists in our extracted data
    found = False
    for idx, row in extracted_debits.iterrows():
        extracted_amount = clean_amount(row['Amount'])
        if abs(extracted_amount - pot['debit']) < 1:  # Allow 1 rupiah difference
            found = True
            break
    
    if not found:
        missing_debits.append(pot)

print(f"\n❌ Found {len(missing_debits)} missing debit(s):")
for i, miss in enumerate(missing_debits):
    print(f"\n  {i+1}. Page {miss['page']}, Line {miss['line_num']}")
    print(f"     Date: {miss['date']}")
    print(f"     Debit: Rp {miss['debit']:,.2f}")
    print(f"     Balance: Rp {miss['balance']:,.2f}")
    print(f"     Desc: {miss['desc']}")

# Also check page 5 specifically since that's where the reverse order bug was
print("\n" + "=" * 80)
print("Checking Page 5 specifically (where reverse order happens)...")
print("=" * 80)

pdf = pdfplumber.open(filepath, password='07031985')
page5 = pdf.pages[4]  # 0-indexed
text5 = page5.extract_text()
lines5 = text5.split('\n')

print(f"\nPage 5 content ({len(lines5)} lines):")
for i, line in enumerate(lines5):
    numbers = re.findall(r'[\d,]+\.[\d]{2}', line)
    if len(numbers) >= 3:
        print(f"  {i:3d}: {line}")

pdf.close()
