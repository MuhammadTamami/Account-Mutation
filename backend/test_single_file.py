"""Test single file upload and download"""
import requests
import pandas as pd

# Test Bank Kalsel file
pdf_path = r'uploads\Acc_Statement_0310073771977_2026-06-01_2026-06-30_20260819134418.pdf'

print("=" * 80)
print("Step 1: Upload and process")
print("=" * 80)

with open(pdf_path, 'rb') as f:
    files = {'file': ('test.pdf', f, 'application/pdf')}
    response = requests.post('http://localhost:5000/api/upload', files=files)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code == 200:
    result = response.json()
    print(f"\nBank: {result.get('bank')}")
    print(f"Transactions: {len(result.get('transactions', []))}")
    
    if len(result.get('transactions', [])) > 0:
        print(f"\nFirst transaction: {result['transactions'][0]}")
        print(f"Last transaction: {result['transactions'][-1]}")
    
    temp_file = result.get('tempFile')
    print(f"\nTemp file: {temp_file}")
    
    # Check temp file content
    if temp_file:
        import os
        temp_path = os.path.join('outputs', temp_file)
        if os.path.exists(temp_path):
            print(f"\n{'=' * 80}")
            print("Temp file content:")
            print('=' * 80)
            df_temp = pd.read_csv(temp_path)
            print(f"Shape: {df_temp.shape}")
            print(f"Columns: {df_temp.columns.tolist()}")
            print(f"\nFirst 5 rows:")
            print(df_temp.head())
            print(f"\nLast 5 rows:")
            print(df_temp.tail())
    
    # Step 2: Download
    print(f"\n{'=' * 80}")
    print("Step 2: Download Excel (daily balance)")
    print('=' * 80)
    
    download_payload = {
        'tempFile': temp_file,
        'mode': 'daily',
        'filters': {}
    }
    
    response = requests.post('http://localhost:5000/api/download/excel', json=download_payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        with open('outputs/test_single.xlsx', 'wb') as f:
            f.write(response.content)
        
        print("Excel saved: outputs/test_single.xlsx")
        
        # Verify
        df_excel = pd.read_excel('outputs/test_single.xlsx', sheet_name='Saldo Harian')
        print(f"\nExcel shape: {df_excel.shape}")
        print(f"Excel columns: {df_excel.columns.tolist()}")
        print(f"\nFirst 5 rows:")
        print(df_excel.head())
    else:
        print(f"Download failed: {response.text[:500]}")
else:
    print("Upload failed!")
