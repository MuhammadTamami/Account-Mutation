"""Test BCA summary extraction"""
from processors.bca_processor import process_bca_pdf

df = process_bca_pdf('../test_data/9. April 2026.pdf')

summary = df.attrs.get('summary', {})

print("\n" + "=" * 80)
print("Summary Extraction Test")
print("=" * 80)

print(f"\nCount CR: {summary.get('count_cr')}")
print(f"Count DB: {summary.get('count_db')}")

if summary.get('mutasi_cr'):
    print(f"Mutasi CR: Rp {summary.get('mutasi_cr'):,.2f}")
else:
    print("Mutasi CR: None")

if summary.get('mutasi_db'):
    print(f"Mutasi DB: Rp {summary.get('mutasi_db'):,.2f}")
else:
    print("Mutasi DB: None")

print("\nActual counts:")
print(f"Credit: {len(df[df['Type'] == 'Credit'])}")
print(f"Debit: {len(df[df['Type'] == 'Debit'])}")
