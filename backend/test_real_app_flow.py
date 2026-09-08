"""
Test script to simulate real app flow: upload -> process -> download Excel
Tests with all available bank data to ensure daily balance export works
"""

import sys
import io
# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import os
import pandas as pd
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_bank_file(pdf_path, bank_name):
    """Test a single PDF file through the complete flow"""
    print(f"\n{'='*80}")
    print(f"Testing: {bank_name} - {os.path.basename(pdf_path)}")
    print('='*80)
    
    # Step 1: Upload and process
    print("\n[STEP 1] Uploading and processing...")
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Process returned {response.status_code}")
        print(response.text)
        return False
    
    result = response.json()
    print(f"✓ Process successful")
    print(f"  Detected bank: {result.get('bank', 'N/A')}")
    print(f"  Transactions: {len(result.get('transactions', []))}")
    print(f"  Temp file: {result.get('tempFile', 'N/A')}")
    
    temp_file = result.get('tempFile')
    if not temp_file:
        print("❌ FAILED: No temp file returned")
        return False
    
    # Step 2: Download Excel (daily balance mode)
    print("\n[STEP 2] Downloading Excel (daily balance)...")
    download_payload = {
        'tempFile': temp_file,
        'mode': 'daily',
        'filters': {}
    }
    
    response = requests.post(
        f"{BASE_URL}/api/download/excel",
        json=download_payload
    )
    
    if response.status_code != 200:
        print(f"❌ FAILED: Download returned {response.status_code}")
        print(response.text)
        return False
    
    # Save Excel file
    output_filename = f"test_output_{bank_name}_{os.path.basename(pdf_path).replace('.pdf', '')}.xlsx"
    output_path = os.path.join('outputs', output_filename)
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    print(f"✓ Excel downloaded: {output_filename}")
    
    # Step 3: Verify Excel content
    print("\n[STEP 3] Verifying Excel content...")
    df = pd.read_excel(output_path, sheet_name='Saldo Harian')
    
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {df.columns.tolist()}")
    
    if df.empty or len(df) == 0:
        print("❌ FAILED: Excel has no data rows!")
        return False
    
    print(f"\n  First 5 rows:")
    print(df.head())
    
    print(f"\n  Last 5 rows:")
    print(df.tail())
    
    # Check for statistics section
    all_data = pd.read_excel(output_path, sheet_name='Saldo Harian', header=None)
    print(f"\n  Total rows in sheet (including stats): {len(all_data)}")
    
    # Look for "Total" row
    total_row_idx = None
    for idx, row in all_data.iterrows():
        if row[0] == 'Total':
            total_row_idx = idx
            break
    
    if total_row_idx:
        print(f"  ✓ Statistics section found at row {total_row_idx + 1}")
        print(f"\n  Statistics:")
        for i in range(total_row_idx, min(total_row_idx + 6, len(all_data))):
            print(f"    {all_data.iloc[i, 0]}: {all_data.iloc[i, 1]}")
    else:
        print(f"  ⚠ No statistics section found")
    
    print(f"\n✅ SUCCESS: {bank_name} - {os.path.basename(pdf_path)}")
    return True

def main():
    # Find all PDF files in uploads directory
    uploads_dir = Path('uploads')
    
    if not uploads_dir.exists():
        print("❌ Uploads directory not found!")
        return
    
    # Get sample PDF files from different banks
    test_files = [
        # Bank Kalsel
        'Acc_Statement_0310073771977_2026-06-01_2026-06-30_20260819134418.pdf',
        'Acc_Statement_0310022490935_2026-07-01_2026-07-31_20260819143344.pdf',
        
        # BCA
        'ESTATEMENT-7326292057-052026-10-13-39.pdf',
        '9. April 2026.pdf',
        
        # BRI  
        '1. 184399112771_e-StatementBRImo_018001000731560_Jan2026_20260728_110025.pdf',
        '2. 184881015933_e-StatementBRImo_018001000731560_Feb2026_20260729_081138.pdf',
        
        # Mandiri
        '1. Mandiri Januari.pdf',
        '2. Mandiri Februari .pdf',
        
        # BYOND (CSV)
        'acct-mutation-3107200133-2026010120260131.csv',
        'acct_mutation_7285137556_2026030120260331.csv',
    ]
    
    results = {
        'passed': [],
        'failed': []
    }
    
    for filename in test_files:
        filepath = uploads_dir / filename
        
        if not filepath.exists():
            print(f"\n⚠ Skipping {filename} - file not found")
            continue
        
        success = test_bank_file(str(filepath), Path(filename).stem)
        
        if success:
            results['passed'].append(filename)
        else:
            results['failed'].append(filename)
    
    
    # Print summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    print(f"\n✅ PASSED ({len(results['passed'])}):")
    for f in results['passed']:
        print(f"  - {f}")
    
    if results['failed']:
        print(f"\n❌ FAILED ({len(results['failed'])}):")
        for f in results['failed']:
            print(f"  - {f}")
    
    total = len(results['passed']) + len(results['failed'])
    print(f"\nTotal: {len(results['passed'])}/{total} passed")
    
    if not results['failed']:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠ {len(results['failed'])} tests failed - check output above")

if __name__ == '__main__':
    main()
