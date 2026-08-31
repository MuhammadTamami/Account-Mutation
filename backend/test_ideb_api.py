"""
Test IDEB SLIK via API
"""
import requests

API_URL = 'http://localhost:5000/api/upload'

# Test IDEB file
print('=== Testing IDEB SLIK API ===\n')
print('📤 Uploading: IDEB PUTRI MAYA.pdf')

with open('../test_data/IDEB PUTRI MAYA.pdf', 'rb') as f:
    files = {'file': ('IDEB PUTRI MAYA.pdf', f, 'application/pdf')}
    response = requests.post(API_URL, files=files)

print(f'\n✓ Status: {response.status_code}')

if response.status_code == 200:
    data = response.json()
    print(f'\n=== Summary ===')
    summary = data['summary']
    print(f"Total Records: {summary['totalRecords']}")
    print(f"File Type: {summary['fileType']}")
    
    print(f'\n=== Data Preview ===')
    if 'data' in data and len(data['data']) > 0:
        print(f"Total credits: {len(data['data'])}")
        print("\nFirst 3 credits:")
        for i, credit in enumerate(data['data'][:3]):
            print(f"\n{i+1}. {credit.get('Nama Bank', 'N/A')}")
            print(f"   Plafon: {credit.get('Plafon', 'N/A')}")
            print(f"   Yield: {credit.get('Yield (%)', 'N/A')}%")
            print(f"   O/S: {credit.get('O/S', 'N/A')}")
            print(f"   Jk Waktu: {credit.get('Jk Waktu', 'N/A')} bulan")
            print(f"   Kol: {credit.get('Kol', 'N/A')}")
    
    print(f"\n✅ IDEB SLIK API Test Passed!")
else:
    print(f'\n❌ Error: {response.text}')
