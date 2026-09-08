"""Test BRI processor to check for missed transactions"""
import sys
sys.path.insert(0, 'processors')

from bri_processor import process_bri_file
import pandas as pd

pdf_path = r'uploads\1. 184399112771_e-StatementBRImo_018001000731560_Jan2026_20260728_110025.pdf'

print("=" * 80)
print("BRI Processor Detail Analysis")
print("=" * 80)

df = process_bri_file(pdf_path, 'pdf')

print(f"\nResults:")
print(f"  Total transactions: {len(df)}")
print(f"  Debit: {len(df[df['Type'] == 'Debit'])}")
print(f"  Credit: {len(df[df['Type'] == 'Credit'])}")

# Check for monthly fees, admin fees, etc
print(f"\n{'='*80}")
print("Checking for fee-related transactions:")
print('='*80)

fee_keywords = ['fee', 'monthly', 'admin', 'biaya', 'tarif', 'charge']

for idx, row in df.iterrows():
    desc_lower = row['Description'].lower()
    if any(keyword in desc_lower for keyword in fee_keywords):
        print(f"{row['Date']} | {row['Type']:6} | {row['Amount']:>15} | {row['Description'][:60]}")

# Show all debit transactions
print(f"\n{'='*80}")
print("All Debit Transactions:")
print('='*80)

debit_df = df[df['Type'] == 'Debit']
for idx, row in debit_df.iterrows():
    print(f"{row['Date']} | {row['Amount']:>15} | {row['Description'][:70]}")

# Show first and last 10 transactions
print(f"\n{'='*80}")
print("First 10 Transactions:")
print('='*80)
print(df[['Date', 'Type', 'Amount', 'Description']].head(10))

print(f"\n{'='*80}")
print("Last 10 Transactions:")
print('='*80)
print(df[['Date', 'Type', 'Amount', 'Description']].tail(10))
