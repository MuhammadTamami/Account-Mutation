# -*- coding: utf-8 -*-
"""
Final test for RK files
"""
import os
import sys
from processors.bank_detector import detect_bank_from_pdf
from processors.mandiri_rk_processor import process_mandiri_rk_file

TEST_DATA_DIR = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data'
test_files = [
    'RK PTBDK.pdf',
    'RK GIRO PTBDK.pdf'
]

print("\n" + "=" * 80)
print("TESTING MANDIRI RK FILES")
print("=" * 80)

for filename in test_files:
    filepath = os.path.join(TEST_DATA_DIR, filename)
    
    print(f"\n{'=' * 80}")
    print(f"File: {filename}")
    print(f"{'=' * 80}")
    
    if not os.path.exists(filepath):
        print(f"ERROR: File not found")
        continue
    
    try:
        # Detect bank
        print("Detecting bank...")
        bank = detect_bank_from_pdf(filepath)
        print(f"Detected: {bank}")
        
        if bank != 'MANDIRI_RK':
            print(f"WARNING: Expected MANDIRI_RK, got {bank}")
        
        # Process
        print(f"\nProcessing...")
        df = process_mandiri_rk_file(filepath, 'pdf')
        
        if df is None or len(df) == 0:
            print(f"ERROR: No data extracted")
            continue
        
        print(f"\nSUCCESS! Extracted {len(df)} transactions")
        
        # Show first 5
        print(f"\nFirst 5 transactions:")
        for i, row in df.head().iterrows():
            print(f"  {i+1}. {row['Date'].strftime('%Y-%m-%d')} | {row['Type']:6s} | {row['Amount']:15s} | {row['Description'][:30]}")
        
        # Summary
        debit_count = len(df[df['Type'] == 'Debit'])
        credit_count = len(df[df['Type'] == 'Credit'])
        print(f"\nSummary:")
        print(f"  Debit:  {debit_count} transactions")
        print(f"  Credit: {credit_count} transactions")
        
        # Save
        output_filename = f"test_output_{filename.replace('.pdf', '').replace(' ', '_')}.csv"
        output_path = os.path.join('outputs', output_filename)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nSaved to: {output_path}")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETED")
print("=" * 80 + "\n")
