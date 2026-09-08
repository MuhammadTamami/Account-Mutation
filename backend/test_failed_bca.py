"""Test failed BCA file"""
import requests

pdf_path = r'uploads\ESTATEMENT-7326292057-052026-10-13-39.pdf'

print("Testing BCA file that failed...")
with open(pdf_path, 'rb') as f:
    files = {'file': ('test.pdf', f, 'application/pdf')}
    response = requests.post('http://localhost:5000/api/upload', files=files)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
