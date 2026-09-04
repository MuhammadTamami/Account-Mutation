"""Test IDEB SUYANTO output"""
from processors.ideb_processor import process_ideb_file, clean_amount
import pandas as pd

# Process the PDF
df = process_ideb_file('../test_data/IDEB SUYANTO.pdf', 'pdf')

print("=" * 80)
print("IDEB SUYANTO - Output Test")
print("=" * 80)

# Display all rows
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

print("\n📋 Data:")
print(df.to_string(index=False))

# Calculate totals
print("\n" + "=" * 80)
print("📊 TOTALS:")
print("=" * 80)

total_plafon = df['Plafon'].apply(lambda x: clean_amount(str(x))).sum()
total_os = df['O/S'].apply(lambda x: clean_amount(str(x))).sum()
total_angsuran = df['Angsuran'].apply(lambda x: clean_amount(str(x))).sum()

print(f"Total Plafon:   Rp {total_plafon:>20,.0f}")
print(f"Total O/S:      Rp {total_os:>20,.0f}")
print(f"Total Angsuran: Rp {total_angsuran:>20,.0f}")

print("\n" + "=" * 80)
print("Expected from manual calculation:")
print("=" * 80)
print(f"Total Plafon:   Rp       5,244,273,900")
print(f"Total O/S:      Rp       4,451,629,582")
print(f"Total Angsuran: Rp         472,575,029")
