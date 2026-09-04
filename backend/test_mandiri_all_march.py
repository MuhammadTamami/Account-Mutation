"""Test all March transactions"""
from processors.mandiri_processor import process_mandiri_pdf

df = process_mandiri_pdf('../test_data/acct_1977_Maret 2026.pdf')

print("=" * 80)
print("MANDIRI MARCH 2026 - Verification")
print("=" * 80)

# Get PDF summary
summary = df.attrs.get('pdf_summary', {})
print("\n📄 PDF Summary:")
print(f"  Expected Debit: {summary.get('no_of_debit', '?')}")
print(f"  Expected Credit: {summary.get('no_of_credit', '?')}")

# Get actual counts
credit_count = len(df[df['Type'] == 'Credit'])
debit_count = len(df[df['Type'] == 'Debit'])

print("\n✓ Actual Extracted:")
print(f"  Debit: {debit_count}")
print(f"  Credit: {credit_count}")

print("\n📊 Comparison:")
if debit_count == summary.get('no_of_debit'):
    print(f"  ✓ Debit: MATCH!")
else:
    print(f"  ✗ Debit: MISMATCH (expected {summary.get('no_of_debit')}, got {debit_count})")
    
if credit_count == summary.get('no_of_credit'):
    print(f"  ✓ Credit: MATCH!")
else:
    print(f"  ✗ Credit: MISMATCH (expected {summary.get('no_of_credit')}, got {credit_count})")

# Show all 24 credits
print(f"\n💰 All {credit_count} Credit transactions:")
credits = df[df['Type'] == 'Credit'].sort_values('Date')
for idx, row in credits.iterrows():
    print(f"  {idx+1:2d}. {row['Date'].strftime('%d/%m/%Y')}: {row['Description'][:45]:45s} Rp {row['Amount']:>15s}")
