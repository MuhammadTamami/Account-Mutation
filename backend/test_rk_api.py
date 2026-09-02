"""
Test RK BDK files via API
"""
import requests
import json
import os

# API endpoint
API_URL = 'http://localhost:5000/api/upload'

# Test files
TEST_DATA_DIR = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data'
test_files = [
    'RK PTBDK.pdf',
    'RK GIRO PTBDK.pdf'
]

def test_upload_file(filename):
    """Test uploading a single file to the API"""
    filepath = os.path.join(TEST_DATA_DIR, filename)
    
    print(f"\n{'=' * 80}")
    print(f"Testing API upload: {filename}")
    print(f"{'=' * 80}")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    try:
        # Upload file
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            response = requests.post(API_URL, files=files)
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ SUCCESS!")
            print(f"\nResponse summary:")
            print(f"  - Success: {data.get('success', False)}")
            
            summary = data.get('summary', {})
            print(f"  - Total Records: {summary.get('totalRecords', 0)}")
            print(f"  - Total Debit: {summary.get('totalDebit', 0)}")
            print(f"  - Total Credit: {summary.get('totalCredit', 0)}")
            print(f"  - Balance: {summary.get('balance', 0)}")
            print(f"  - File Type: {summary.get('fileType', 'Unknown')}")
            print(f"  - Date Range: {summary.get('dateRange', {}).get('start', '?')} to {summary.get('dateRange', {}).get('end', '?')}")
            
            # Account info
            account_info = data.get('accountInfo')
            if account_info:
                print(f"\nAccount Info:")
                print(f"  - Account Number: {account_info.get('accountNumber', '?')}")
                print(f"  - Name: {account_info.get('name', '?')}")
                print(f"  - Branch: {account_info.get('branch', '?')}")
            
            # Show first 5 transactions
            all_data = data.get('allData', [])
            if all_data:
                print(f"\nFirst 5 transactions:")
                for i, txn in enumerate(all_data[:5], 1):
                    print(f"  {i}. {txn.get('Date')} | {txn.get('Type')} | {txn.get('Amount')} | {txn.get('Description')}")
            
            # Monthly summary
            monthly_summary = data.get('monthlySummary', [])
            if monthly_summary:
                print(f"\nMonthly Summary:")
                for month in monthly_summary:
                    print(f"  - {month.get('monthName')}: Debit={month.get('freqDebit')} ({month.get('totalDebit')}), Credit={month.get('freqCredit')} ({month.get('totalCredit')})")
            
            return True
        else:
            print(f"❌ FAILED!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "🚀 " * 40)
    print("TESTING RK BDK FILES VIA API")
    print("🚀 " * 40)
    
    # Check if API is running
    try:
        response = requests.get('http://localhost:5000/')
        print(f"\n✓ API is running")
    except:
        print(f"\n❌ API is not running!")
        print(f"   Please start the API first: python app.py")
        return
    
    # Test each file
    results = []
    for filename in test_files:
        success = test_upload_file(filename)
        results.append((filename, success))
    
    # Summary
    print(f"\n{'=' * 80}")
    print(f"TEST SUMMARY")
    print(f"{'=' * 80}")
    for filename, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {filename}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\nTotal: {passed}/{total} passed")
    
    print(f"\n{'✅ ' * 40}")
    print(f"API TEST COMPLETED")
    print(f"{'✅ ' * 40}\n")

if __name__ == "__main__":
    main()
