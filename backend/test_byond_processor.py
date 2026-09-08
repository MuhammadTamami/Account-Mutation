"""Test BYOND processor with the failed file"""
import sys
sys.path.insert(0, 'processors')

from byond_processor import process_byond_file

pdf_path = r'uploads\ESTATEMENT-7326292057-052026-10-13-39.pdf'

print("=" * 80)
print("Testing BYOND Processor")
print("=" * 80)

df = process_byond_file(pdf_path, 'pdf')

print(f"\nResult:")
print(f"  Rows: {len(df)}")
print(f"  Columns: {df.columns.tolist() if len(df) > 0 else 'N/A'}")

if len(df) > 0:
    print(f"\nFirst 5 transactions:")
    print(df.head())
    
    print(f"\nLast 5 transactions:")
    print(df.tail())
    
    print(f"\nDebit count: {len(df[df['Type'] == 'Debit'])}")
    print(f"Credit count: {len(df[df['Type'] == 'Credit'])}")
else:
    print("\n❌ No data extracted!")
