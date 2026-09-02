# -*- coding: utf-8 -*-
"""
Verify January transactions for RK GIRO
"""
from processors.mandiri_rk_processor import process_mandiri_rk_file
import pandas as pd

filepath = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\RK GIRO PTBDK.pdf'

print("Processing RK GIRO PTBDK.pdf...")
df = process_mandiri_rk_file(filepath, 'pdf')

if df is not None:
    print(f"\nTotal transactions: {len(df)}")
    
    # Filter January 2025
    df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')
    jan_2025 = df[df['Month'] == '2025-01']
    
    print(f"\nJanuary 2025 transactions: {len(jan_2025)}")
    print("\nJanuary transactions detail:")
    print("=" * 100)
    
    for i, row in jan_2025.iterrows():
        date_str = row['Date'].strftime('%Y-%m-%d')
        print(f"{date_str} | {row['Type']:6s} | {row['Amount']:20s} | {row['Balance']:20s} | {row['Description'][:40]}")
    
    print("=" * 100)
    
    # Summary for January
    jan_debit = jan_2025[jan_2025['Type'] == 'Debit']
    jan_credit = jan_2025[jan_2025['Type'] == 'Credit']
    
    print(f"\nJanuary Summary:")
    print(f"  Debit:  {len(jan_debit)} transactions")
    print(f"  Credit: {len(jan_credit)} transactions")
    
    # First and last balance
    if len(jan_2025) > 0:
        first_balance = jan_2025.iloc[0]['Balance']
        last_balance = jan_2025.iloc[-1]['Balance']
        print(f"\nBalances:")
        print(f"  First transaction (14/01): {first_balance}")
        print(f"  Last transaction (31/01):  {last_balance}")
        print(f"  Expected last balance:      515072640,43")
else:
    print("ERROR: No data extracted")
