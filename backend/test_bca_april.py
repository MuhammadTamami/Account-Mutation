"""Test BCA April 2026 file"""
from processors.bca_processor import process_bca_pdf

filepath = '../test_data/9. April 2026.pdf'

print("=" * 80)
print("Testing BCA April 2026")
print("=" * 80)

df = process_bca_pdf(filepath)

if len(df) == 0:
    print("\nNo data extracted!")
else:
    print(f"\nTotal records: {len(df)}")
    
    # Count by type
    credit_count = len(df[df['Type'] == 'Credit'])
    debit_count = len(df[df['Type'] == 'Debit'])
    
    print(f"Credit transactions: {credit_count}")
    print(f"Debit transactions: {debit_count}")
    
    # Calculate totals
    def parse_amount(val):
        if not val or val == '-' or val == '0.00':
            return 0.0
        val_str = str(val).replace(',', '').replace('.', '')
        # Last 2 digits are cents
        if len(val_str) >= 2:
            return float(val_str[:-2] + '.' + val_str[-2:])
        return 0.0
    
    total_credit = df[df['Type'] == 'Credit']['Amount'].apply(parse_amount).sum()
    total_debit = df[df['Type'] == 'Debit']['Amount'].apply(parse_amount).sum()
    
    print(f"\nTotal Credit: Rp {total_credit:,.2f}")
    print(f"Total Debit: Rp {total_debit:,.2f}")
    
    # Expected from PDF
    print("\n" + "=" * 80)
    print("Expected from PDF:")
    print("=" * 80)
    print("MUTASI CR: 1,880,194,638.18 (631 transactions)")
    print("MUTASI DB: 1,822,464,652.25 (34 transactions)")
    
    # Check balance column
    print("\n" + "=" * 80)
    print("Checking Balance column:")
    print("=" * 80)
    if 'Balance' in df.columns:
        non_zero_balance = df[df['Balance'] != '0.00']
        print(f"Rows with non-zero balance: {len(non_zero_balance)}")
        print(f"Rows with zero balance: {len(df) - len(non_zero_balance)}")
        
        if len(non_zero_balance) > 0:
            print("\nFirst 5 non-zero balances:")
            for idx, row in non_zero_balance.head(5).iterrows():
                print(f"  {row['Date']}: {row['Balance']}")
        else:
            print("\nALL BALANCES ARE 0.00! This is the problem!")
    else:
        print("No Balance column found!")
    
    # Show first 10 transactions
    print("\n" + "=" * 80)
    print("First 10 transactions:")
    print("=" * 80)
    for idx, row in df.head(10).iterrows():
        print(f"{row['Date']} {row['Type']:6s}: {row['Description'][:40]:40s} Rp {row['Amount']:>15s} | Bal: {row.get('Balance', 'N/A')}")
