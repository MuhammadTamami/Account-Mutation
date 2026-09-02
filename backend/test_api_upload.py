# -*- coding: utf-8 -*-
"""
Test API upload for RK files
"""
import requests
import os

API_URL = 'http://localhost:5000/api/upload'
TEST_DATA_DIR = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data'

def test_upload(filename):
    """Test uploading a file"""
    filepath = os.path.join(TEST_DATA_DIR, filename)
    
    print(f"\n{'=' * 80}")
    print(f"Testing: {filename}")
    print(f"{'=' * 80}")
    
    if not os.path.exists(filepath):
        print(f"ERROR: File not found")
        return False
    
    try:
        # Upload file
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            print(f"Uploading to {API_URL}...")
            response = requests.post(API_URL, files=files, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nSUCCESS!")
            
            summary = data.get('summary', {})
            print(f"\nSummary:")
            print(f"  Total Records: {summary.get('totalRecords', 0)}")
            print(f"  Total Debit:   {summary.get('totalDebit', 0)}")
            print(f"  Total Credit:  {summary.get('totalCredit', 0)}")
            print(f"  File Type:     {summary.get('fileType', 'Unknown')}")
            print(f"  Date Range:    {summary.get('dateRange', {}).get('start', '?')} to {summary.get('dateRange', {}).get('end', '?')}")
            
            # Account info
            account_info = data.get('accountInfo')
            if account_info:
                print(f"\nAccount Info:")
                print(f"  Account Number: {account_info.get('accountNumber', '?')}")
                print(f"  Name: {account_info.get('name', '?')}")
            
            return True
        else:
            print(f"\nFAILED!")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Cannot connect to {API_URL}")
        print(f"Please start the server first: python app.py")
        return False
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TESTING API UPLOAD")
    print("=" * 80)
    
    test_files = [
        'RK PTBDK.pdf',
        'RK GIRO PTBDK.pdf'
    ]
    
    results = []
    for filename in test_files:
        success = test_upload(filename)
        results.append((filename, success))
    
    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"{'=' * 80}")
    for filename, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {status:6s} - {filename}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\nTotal: {passed}/{total} passed")
    print("=" * 80 + "\n")
