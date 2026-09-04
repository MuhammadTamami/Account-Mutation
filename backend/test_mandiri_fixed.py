"""Test fixed Mandiri processor"""
from processors.mandiri_processor import process_mandiri_pdf

df = process_mandiri_pdf('../test_data/acct_1977_Maret 2026.pdf')

print(f'Total records: {len(df)}')
credit_count = len(df[df['Type'] == 'Credit'])
debit_count = len(df[df['Type'] == 'Debit'])
print(f'Credit: {credit_count}')
print(f'Debit: {debit_count}')

print('\nLast 3 credits:')
credits = df[df['Type'] == 'Credit'].tail(3)
for idx, row in credits.iterrows():
    print(f'  {row["Date"].strftime("%d/%m/%Y")}: {row["Description"][:50]:50s} Rp {row["Amount"]}')
