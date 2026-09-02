# -*- coding: utf-8 -*-
"""
Debug February transactions for RK GIRO
"""
from processors.mandiri_rk_processor import process_mandiri_rk_file
import pandas as pd

filepath = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\RK GIRO PTBDK.pdf'

print("Processing RK GIRO PTBDK.pdf...")
df = process_mandiri_rk_file(filepath, 'pdf')

if df is not None:
    print(f"\nTotal transactions: {len(df)}")
    
    # Filter February 2025
    df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')
    feb_2025 = df[df['Month'] == '2025-02']
    
    print(f"\nFebruary 2025 transactions: {len(feb_2025)}")
    print("\nFebruary transactions detail:")
    print("=" * 120)
    
    for i, row in feb_2025.iterrows():
        date_str = row['Date'].strftime('%Y-%m-%d')
        print(f"{date_str} | {row['Type']:6s} | Amount: {row['Amount']:20s} | Balance: {row['Balance']:20s} | {row['Description'][:50]}")
    
    print("=" * 120)
    
    # Check last balance on Feb 28
    feb_28 = feb_2025[pd.to_datetime(feb_2025['Date']).dt.day == 28]
    if len(feb_28) > 0:
        print(f"\nTransactions on Feb 28: {len(feb_28)}")
        last_balance = feb_28.iloc[-1]['Balance']
        print(f"Last balance on Feb 28: {last_balance}")
        print(f"Expected: 539742049,24")
        
        if last_balance == '539742049,24':
            print("✅ MATCH!")
        else:
            print("❌ MISMATCH!")
else:
    print("ERROR: No data extracted")
