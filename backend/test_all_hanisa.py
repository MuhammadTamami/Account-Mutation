"""Test all Hanisa files"""
import sys
sys.path.insert(0, 'processors')

from bri_processor import process_bri_file
from pathlib import Path

hanisa_files = [
    'uploads/HANISA JANUARI.pdf',
    'uploads/HANISA FEBRUARI.pdf',
    'uploads/HANISA JULI.pdf',
    'uploads/HANISA AGUSTUS.pdf',
]

print("=" * 80)
print("Testing All Hanisa Files")
print("=" * 80)

for pdf_path in hanisa_files:
    if not Path(pdf_path).exists():
        print(f"\n⚠ File not found: {pdf_path}")
        continue
    
    print(f"\n{'='*80}")
    print(f"File: {Path(pdf_path).name}")
    print('='*80)
    
    df = process_bri_file(pdf_path, 'pdf')
    
    print(f"Total: {len(df)}, Debit: {len(df[df['Type'] == 'Debit'])}, Credit: {len(df[df['Type'] == 'Credit'])}")
    
    # Look for fee transactions
    fee_transactions = df[df['Description'].str.lower().str.contains('fee|biaya|tarif|admin|monthly', na=False)]
    
    if len(fee_transactions) > 0:
        print(f"\n✓ Found {len(fee_transactions)} fee-related transactions:")
        for idx, row in fee_transactions.iterrows():
            print(f"  {row['Date']} | {row['Type']:6} | {row['Amount']:>15} | {row['Description']}")
    else:
        print(f"\n  No fee-related transactions found")
    
    # Show all transactions
    print(f"\nAll Transactions:")
    for idx, row in df.iterrows():
        print(f"  {row['Date']} | {row['Type']:6} | {row['Amount']:>15} | {row['Description'][:60]}")

print(f"\n{'='*80}")
print("Test Complete")
