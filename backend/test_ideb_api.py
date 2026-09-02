# -*- coding: utf-8 -*-
"""
Test IDEB API upload
"""
import requests

url = 'http://localhost:5000/api/upload'

# Test IDEB file
file_path = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\IDEB PUTRI MAYA.pdf'

with open(file_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nMode: {data.get('mode')}")
    print(f"Credits found: {len(data.get('data', []))}")
    
    if len(data.get('data', [])) > 0:
        print(f"\nFirst credit columns:")
        first_credit = data['data'][0]
        for key, value in first_credit.items():
            print(f"  {key}: {value}")
else:
    print(f"Error: {response.text}")
