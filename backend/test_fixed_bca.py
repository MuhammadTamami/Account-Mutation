"""Test the fixed 'BCA' file (actually BYOND) through full flow"""
import requests
import pandas as pd

pdf_path = r'uploads\ESTATEMENT-7326292057-052026-10-13-39.pdf'

print("=" * 80)
print("Testing 'BCA' File (Actually BYOND) - Full Flow")
print("=" * 80)

# Step 1: Upload
print("\n[STEP 1] Uploading...")
with open(pdf_path, 'rb') as f:
    files = {'file': ('test.pdf', f, 'application/pdf')}
    response = requests.post('http://localhost:5000/api/upload', files=files)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"✓ Upload successful")
    print(f"  Bank detected: {result.get('bank', 'N/A')}")
    print(f"  Account: {result.get('accountInfo', {}).get('name', 'N/A')}")
    print(f"  Temp file: {result.get('tempFile', 'N/A')}")
    
    # Check temp CSV
    temp_file = result.get('tempFile')
    if temp_file:
        import os
        temp_path = os.path.join('outputs', temp_file)
        if os.path.exists(temp_path):
            df_temp = pd.read_csv(temp_path)
            print(f"\n  Temp CSV: {df_temp.shape[0]} rows")
            print(f"  Debit: {len(df_temp[df_temp['Type'].str.lower() == 'debit'])}")
            print(f"  Credit: {len(df_temp[df_temp['Type'].str.lower() == 'credit'])}")
    
    # Step 2: Download daily balance Excel
    print(f"\n[STEP 2] Downloading daily balance Excel...")
    download_payload = {
        'tempFile': temp_file,
        'mode': 'daily',
        'filters': {}
    }
    
    response = requests.post('http://localhost:5000/api/download/excel', json=download_payload)
    
    if response.status_code == 200:
        output_file = 'outputs/test_byond_fixed.xlsx'
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Excel downloaded: {output_file}")
        
        # Verify content
        df_excel = pd.read_excel(output_file, sheet_name='Saldo Harian')
        print(f"\n[STEP 3] Verifying Excel...")
        print(f"  Shape: {df_excel.shape}")
        print(f"  Columns: {df_excel.columns.tolist()}")
        
        print(f"\n  First 5 rows:")
        print(df_excel.head())
        
        print(f"\n  Last 5 rows:")
        print(df_excel.tail())
        
        # Check mutation statistics
        df_full = pd.read_excel(output_file, sheet_name='Saldo Harian', header=None)
        print(f"\n  Mutation statistics:")
        for idx in range(len(df_full) - 10, len(df_full)):
            if idx >= 0:
                row = df_full.iloc[idx]
                if not pd.isna(row[0]):
                    print(f"    {row[0]}: {row[1]}")
        
        print(f"\n✅ SUCCESS: File processed correctly as BYOND!")
    else:
        print(f"❌ Download failed: {response.status_code}")
        print(response.text)
else:
    print(f"❌ Upload failed: {response.status_code}")
    print(response.text[:500])
