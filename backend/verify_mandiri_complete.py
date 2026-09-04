"""Complete verification of Mandiri March 1977"""
from processors.mandiri_processor import process_mandiri_pdf, clean_amount

df = process_mandiri_pdf('../test_data/acct_1977_Maret 2026.pdf')

print("=" * 80)
print("FINAL VERIFICATION: Mandiri March 2026")
print("=" * 80)

summary = df.attrs.get('pdf_summary', {})

print("\n📄 PDF Summary (Expected):")
print(f"  Debit: {summary.get('no_of_debit')}")
print(f"  Credit: {summary.get('no_of_credit')}")
print(f"  Total: {summary.get('no_of_debit') + summary.get('no_of_credit')}")

actual_debit = len(df[df['Type'] == 'Debit'])
actual_credit = len(df[df['Type'] == 'Credit'])

print("\n✓ Actual Extracted:")
print(f"  Debit: {actual_debit}")
print(f"  Credit: {actual_credit}")
print(f"  Total: {len(df)}")

print("\n📊 Verification:")
debit_match = "✓ MATCH!" if actual_debit == summary.get('no_of_debit') else f"✗ MISMATCH (diff: {actual_debit - summary.get('no_of_debit')})"
credit_match = "✓ MATCH!" if actual_credit == summary.get('no_of_credit') else f"✗ MISMATCH (diff: {actual_credit - summary.get('no_of_credit')})"

print(f"  Debit:  {debit_match}")
print(f"  Credit: {credit_match}")

# Show last 5 transactions (should include Bunga and Pajak)
print("\n📋 Last 5 transactions:")
last_5 = df.tail(5)
for idx, row in last_5.iterrows():
    print(f"  {row['Date'].strftime('%d/%m/%Y')} {row['Type']:6s}: {row['Description'][:40]:40s} Rp {row['Amount']:>15s}")

# Specifically check for Bunga and Pajak
print("\n🔍 Checking Page 5 special transactions:")
bunga = df[df['Description'].str.contains('Bunga', case=False, na=False)]
pajak = df[df['Description'].str.contains('Pajak', case=False, na=False)]

if len(bunga) > 0:
    print("  ✓ Bunga found:")
    for idx, row in bunga.iterrows():
        print(f"    {row['Date'].strftime('%d/%m/%Y')} {row['Type']:6s}: {row['Description']:30s} Rp {row['Amount']}")
else:
    print("  ✗ Bunga NOT found!")

if len(pajak) > 0:
    print("  ✓ Pajak found:")
    for idx, row in pajak.iterrows():
        print(f"    {row['Date'].strftime('%d/%m/%Y')} {row['Type']:6s}: {row['Description']:30s} Rp {row['Amount']}")
else:
    print("  ✗ Pajak NOT found!")

print("\n" + "=" * 80)
if actual_debit == summary.get('no_of_debit') and actual_credit == summary.get('no_of_credit'):
    print("✅ ALL CHECKS PASSED! Mandiri parser is working correctly!")
else:
    print("❌ STILL HAVE ISSUES")
print("=" * 80)
