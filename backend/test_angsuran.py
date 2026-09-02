# -*- coding: utf-8 -*-
"""
Test Angsuran calculation in IDEB
"""
from processors.ideb_processor import process_ideb_file

filepath = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\IDEB PUTRI MAYA.pdf'

df = process_ideb_file(filepath, 'pdf')

print(f"Columns: {df.columns.tolist()}\n")
print("="*120)
print(f"{'Nama Bank':<35} | {'Plafon':>20} | {'Yield':>8} | {'Jk Waktu':>8} | {'Angsuran':>20}")
print("="*120)

total_plafon = 0
total_os = 0
total_angsuran = 0

for i, row in df.iterrows():
    print(f"{row['Nama Bank']:<35} | {row['Plafon']:>20} | {row['Yield (%)']:>8} | {row['Jk Waktu']:>8} | {row['Angsuran']:>20}")
    
    # Parse for totals
    from processors.ideb_processor import clean_amount
    plafon_val = clean_amount(row['Plafon'].replace(',', '.'))
    os_val = clean_amount(row['O/S'].replace(',', '.'))
    angsuran_val = clean_amount(row['Angsuran'].replace(',', '.'))
    
    total_plafon += plafon_val
    total_os += os_val
    total_angsuran += angsuran_val

print("="*120)
print(f"{'TOTAL':<35} | {total_plafon:>20,.2f} | {'':<8} | {'':<8} | {total_angsuran:>20,.2f}")
print("="*120)
print(f"\nTotal O/S: {total_os:,.2f}")
