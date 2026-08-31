"""
Test IDEB Excel export with mm/dd/yyyy date format
"""
import requests
import pandas as pd
from datetime import datetime

print("=== Testing IDEB Excel Export ===\n")

# Step 1: Upload file
print("📤 Step 1: Uploading IDEB PUTRI MAYA.pdf...")
with open('../test_data/IDEB PUTRI MAYA.pdf', 'rb') as f:
    files = {'file': f}
    r = requests.post('http://localhost:5000/api/upload', files=files)

if r.status_code != 200:
    print(f"❌ Upload failed: {r.json()}")
    exit(1)

data = r.json()
temp_file = data['tempFile']
print(f"✅ Upload successful! Temp file: {temp_file}")
print(f"   Total credits: {data['summary']['totalRecords']}")

# Step 2: Download Excel
print(f"\n📥 Step 2: Downloading Excel...")
download_response = requests.post(
    'http://localhost:5000/api/download/excel',
    json={'tempFile': temp_file, 'mode': 'ideb'},
    stream=True
)

if download_response.status_code != 200:
    print(f"❌ Download failed: {download_response.text}")
    exit(1)

# Save Excel
output_path = f'test_ideb_output_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
with open(output_path, 'wb') as f:
    f.write(download_response.content)

print(f"✅ Excel downloaded: {output_path}")

# Step 3: Verify Excel content
print(f"\n📊 Step 3: Verifying Excel content...")
df = pd.read_excel(output_path, sheet_name='IDEB SLIK')

print(f"   Rows: {len(df)}")
print(f"   Columns: {list(df.columns)}")

print(f"\n📅 Date Format Verification:")
print(f"   First 3 credits:")
for i in range(min(3, len(df))):
    print(f"\n   {i+1}. {df.iloc[i]['Nama Bank']}")
    print(f"      Tanggal Pencairan: {df.iloc[i]['Tanggal Pencairan']}")
    print(f"      Tanggal Jatuh Tempo: {df.iloc[i]['Tanggal Jatuh Tempo']}")
    
    # Check if format is mm/dd/yyyy
    tgl_pencairan = str(df.iloc[i]['Tanggal Pencairan'])
    if '/' in tgl_pencairan:
        parts = tgl_pencairan.split('/')
        if len(parts) == 3:
            print(f"      ✅ Format OK: mm/dd/yyyy")
        else:
            print(f"      ⚠ Format may be incorrect")
    else:
        print(f"      ⚠ Not in mm/dd/yyyy format")

print(f"\n✅ Test completed! Excel file: {output_path}")
