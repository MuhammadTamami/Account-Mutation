"""Verify mutation calculations"""
import pandas as pd

# Read CSV
df = pd.read_csv('outputs/temp_20260907110534.csv')

print("=" * 80)
print("Mutation Verification")
print("=" * 80)

# Count and sum debit transactions
debit_df = df[df['Type'].str.lower().str.strip() == 'debit']
credit_df = df[df['Type'].str.lower().str.strip() == 'credit']

print(f"\nDebit Transactions: {len(debit_df)}")
print(f"Credit Transactions: {len(credit_df)}")

# Parse amounts
def parse_amount(val):
    if pd.isna(val) or val == '' or val == '-':
        return 0.0
    val_str = str(val).strip().replace('Rp', '').replace(' ', '').strip()
    
    # Handle different formats
    if ',' in val_str and '.' in val_str:
        last_comma_pos = val_str.rfind(',')
        last_dot_pos = val_str.rfind('.')
        
        if last_dot_pos > last_comma_pos:
            # International: 1,234,567.89
            val_str = val_str.replace(',', '')
        else:
            # Indonesian: 1.234.567,89
            val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
    elif '.' in val_str:
        last_dot_pos = val_str.rfind('.')
        decimal_part_length = len(val_str) - last_dot_pos - 1
        if decimal_part_length == 2:
            val_str = val_str[:last_dot_pos].replace('.', '') + '.' + val_str[last_dot_pos+1:]
        else:
            val_str = val_str.replace('.', '')
    
    try:
        return float(val_str)
    except:
        return 0.0

# Calculate totals
debit_df['Amount_numeric'] = debit_df['Amount'].apply(parse_amount)
credit_df['Amount_numeric'] = credit_df['Amount'].apply(parse_amount)

total_debit = debit_df['Amount_numeric'].sum()
total_credit = credit_df['Amount_numeric'].sum()

print(f"\nTotal Debit: Rp {total_debit:,.2f}")
print(f"Total Credit: Rp {total_credit:,.2f}")

print(f"\nTop 5 Debit transactions:")
print(debit_df[['Date', 'Description', 'Amount']].head())

print(f"\nTop 5 Credit transactions:")
print(credit_df[['Date', 'Description', 'Amount']].head())
