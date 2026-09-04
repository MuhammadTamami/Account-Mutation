"""Analyze BCA extraction results"""
from processors.bca_processor import process_bca_pdf

df = process_bca_pdf('../test_data/9. April 2026.pdf')

print("\n" + "=" * 80)
print("BCA Extraction Analysis")
print("=" * 80)

print(f"\nTotal extracted: {len(df)}")
print(f"Credit: {len(df[df['Type'] == 'Credit'])}")
print(f"Debit: {len(df[df['Type'] == 'Debit'])}")

# Show all Debit transactions
print("\n" + "=" * 80)
print("All DEBIT transactions:")
print("=" * 80)
debits = df[df['Type'] == 'Debit']
for idx, row in debits.iterrows():
    print(f"{row['Date'].strftime('%d/%m')}: {row['Description'][:50]:50s} Rp {row['Amount']:>15s}")

# Check for potential duplicates
print("\n" + "=" * 80)
print("Checking for duplicates (same date + amount):")
print("=" * 80)
dup_count = 0
for idx, row in df.iterrows():
    same = df[(df['Date'] == row['Date']) & (df['Amount'] == row['Amount']) & (df.index != idx)]
    if len(same) > 0:
        dup_count += 1
        if dup_count <= 5:  # Show first 5
            print(f"\nDuplicate {dup_count}:")
            print(f"  {row['Date'].strftime('%d/%m')} {row['Type']}: {row['Description'][:40]} Rp {row['Amount']}")
            for _, s in same.iterrows():
                print(f"  {s['Date'].strftime('%d/%m')} {s['Type']}: {s['Description'][:40]} Rp {s['Amount']}")

print(f"\nTotal potential duplicates: {dup_count}")

# Look for "TRSF E-BANKING DB" in descriptions
print("\n" + "=" * 80)
print("Transactions with 'TRSF E-BANKING DB' in description:")
print("=" * 80)
trsf_db = df[df['Description'].str.contains('TRSF E-BANKING DB', case=False, na=False)]
print(f"Found: {len(trsf_db)}")
for idx, row in trsf_db.head(10).iterrows():
    print(f"{row['Date'].strftime('%d/%m')} {row['Type']:6s}: {row['Description'][:50]:50s} Rp {row['Amount']:>15s}")
