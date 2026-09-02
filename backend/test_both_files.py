# -*- coding: utf-8 -*-
"""
Test both RK PTBDK and RK GIRO files
"""
from processors.mandiri_rk_processor import process_mandiri_rk_file
import pandas as pd

files = [
    ('RK PTBDK', r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\RK PTBDK.pdf'),
    ('RK GIRO PTBDK', r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\RK GIRO PTBDK.pdf')
]

for name, filepath in files:
    print("\n" + "="*80)
    print(f"Testing: {name}")
    print("="*80)
    
    df = process_mandiri_rk_file(filepath, 'pdf')
    
    if df is not None:
        print(f"\nTotal transactions: {len(df)}")
        
        # Filter January 2025
        df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')
        jan_2025 = df[df['Month'] == '2025-01']
        
        print(f"January 2025 transactions: {len(jan_2025)}")
        
        if len(jan_2025) > 0:
            print("\nFirst 5 January transactions:")
            for i, row in jan_2025.head(5).iterrows():
                date_str = row['Date'].strftime('%Y-%m-%d')
                print(f"  {date_str} | {row['Type']:7s} | {row['Balance']:20s} | {row['Description'][:40]}")
            
            # Summary
            jan_debit = jan_2025[jan_2025['Type'] == 'Debit']
            jan_credit = jan_2025[jan_2025['Type'] == 'Credit']
            jan_balance = jan_2025[jan_2025['Type'] == 'Balance']
            
            print(f"\nJanuary Summary:")
            print(f"  Balance entries: {len(jan_balance)}")
            print(f"  Debit:  {len(jan_debit)} transactions")
            print(f"  Credit: {len(jan_credit)} transactions")
    else:
        print("ERROR: No data extracted")

print("\n" + "="*80)
