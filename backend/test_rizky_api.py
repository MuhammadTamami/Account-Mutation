import requests

print("=== Testing IDEB RIZKY ADE via API ===\n")

with open('../test_data/IDEB RIZKY ADE.pdf', 'rb') as f:
    files = {'file': f}
    r = requests.post('http://localhost:5000/api/upload', files=files)

print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"\n✅ Success!")
    print(f"Mode: {data.get('mode', 'N/A')}")
    print(f"Total credits: {data['summary']['totalRecords']}")
    
    # Show first 5
    print(f"\nFirst 5 credits:")
    for i, credit in enumerate(data['data'][:5], 1):
        print(f"{i}. {credit['Nama Bank']}")
        print(f"   Plafon: {credit['Plafon']}")
        print(f"   O/S: {credit['O/S']}")
        print()
else:
    print(f"\n❌ Error: {r.json()}")
