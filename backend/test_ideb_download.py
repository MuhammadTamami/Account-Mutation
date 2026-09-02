# -*- coding: utf-8 -*-
"""
Test IDEB download with Total row
"""
import requests
import json

# Step 1: Upload IDEB file
print("Step 1: Uploading IDEB file...")
upload_url = 'http://localhost:5000/api/upload'
file_path = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\IDEB PUTRI MAYA.pdf'

with open(file_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(upload_url, files=files)

if response.status_code != 200:
    print(f"Upload failed: {response.text}")
    exit(1)

data = response.json()
temp_file = data.get('tempFile')
print(f"✓ Upload success. Temp file: {temp_file}")
print(f"✓ Credits found: {len(data.get('data', []))}")

# Step 2: Download as Excel
print("\nStep 2: Downloading as Excel...")
download_url = 'http://localhost:5000/api/download/excel'

payload = {
    'tempFile': temp_file,
    'mode': 'ideb'
}

response = requests.post(download_url, json=payload)

if response.status_code == 200:
    output_file = 'test_ideb_with_total.xlsx'
    with open(output_file, 'wb') as f:
        f.write(response.content)
    print(f"✓ Excel downloaded: {output_file}")
    print(f"  File size: {len(response.content)} bytes")
else:
    print(f"Download failed: {response.status_code} - {response.text}")

# Step 3: Download as CSV
print("\nStep 3: Downloading as CSV...")
download_url_csv = 'http://localhost:5000/api/download/csv'

response_csv = requests.post(download_url_csv, json=payload)

if response_csv.status_code == 200:
    output_file_csv = 'test_ideb_with_total.csv'
    with open(output_file_csv, 'wb') as f:
        f.write(response_csv.content)
    print(f"✓ CSV downloaded: {output_file_csv}")
    print(f"  File size: {len(response_csv.content)} bytes")
    
    # Read and display CSV content
    print("\nCSV Content:")
    print(response_csv.content.decode('utf-8'))
else:
    print(f"Download failed: {response_csv.status_code} - {response_csv.text}")
