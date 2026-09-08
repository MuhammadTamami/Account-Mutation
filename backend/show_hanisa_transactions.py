"""Show extracted Hanisa transactions"""
import sys
sys.path.insert(0, 'processors')

from bri_processor import process_bri_file

pdf_path = r'uploads\HANISA JANUARI.pdf'

df = process_bri_file(pdf_path, 'pdf')

print("Extracted Transactions:")
print("=" * 80)
for idx, row in df.iterrows():
    print(f"{row['Date']} | {row['Type']:6} | {row['Amount']:>15} | {row['Description']}")
