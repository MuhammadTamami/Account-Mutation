# -*- coding: utf-8 -*-
"""
Simple OCR test for scanned RK files
"""
import os
import sys

TEST_DATA_DIR = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data'
test_files = [
    'Rekening koran bdk 2025.pdf',
    'Rekening Koran BDK Jan - Juli 2026.pdf'
]

def test_file(filename):
    """Test OCR processing for a single file"""
    from processors.mandiri_rk_ocr_processor import process_mandiri_rk_ocr_file
    
    filepath = os.path.join(TEST_DATA_DIR, filename)
    
    print("\n" + "=" * 80)
    print(f"Processing: {filename}")
    print("=" * 80)
    
    if not os.path.exists(filepath):
        print(f"ERROR: File not found")
        return False
    
    try:
        print(f"Starting OCR processing (this may take 30-60 seconds)...")
        
        # Process file with OCR
        df = process_mandiri_rk_ocr_file(filepath, 'pdf')
        
        if df is None or len(df) == 0:
            print(f"\nERROR: No data extracted")
            return False
        
        print(f"\nSUCCESS! Extracted {len(df)} transactions")
        
        print(f"\nFirst 10 rows:")
        print(df.head(10).to_string())
        
        print(f"\nColumn names:")
        print(df.columns.tolist())
        
        # Summary
        if 'Type' in df.columns:
            print(f"\nTransaction summary:")
            print(f"  Total Debit: {len(df[df['Type'] == 'Debit'])} transactions")
            print(f"  Total Credit: {len(df[df['Type'] == 'Credit'])} transactions")
        
        # Save to CSV
        output_filename = f"test_output_OCR_{filename.replace('.pdf', '').replace(' ', '_')}.csv"
        output_path = os.path.join('outputs', output_filename)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nSaved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TESTING OCR PROCESSING FOR SCANNED RK FILES")
    print("=" * 80)
    
    results = []
    for filename in test_files:
        success = test_file(filename)
        results.append((filename, success))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for filename, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status:6s} - {filename}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\nTotal: {passed}/{total} passed")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)
