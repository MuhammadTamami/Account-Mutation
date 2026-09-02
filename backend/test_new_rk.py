"""
Test script untuk file rekening koran BDK baru
File yang akan ditest:
1. RK PTBDK.pdf
2. Rekening Koran BDK Jan - Juli 2026.pdf
3. RK GIRO PTBDK.pdf
"""

import os
import sys
from processors.bank_detector import detect_bank_from_pdf

# File paths
TEST_DATA_DIR = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data'
test_files = [
    'RK PTBDK.pdf',
    'Rekening Koran BDK Jan - Juli 2026.pdf',
    'RK GIRO PTBDK.pdf'
]

def test_bank_detection():
    """Test bank detection for new RK files"""
    print("=" * 80)
    print("TESTING BANK DETECTION FOR NEW RK FILES")
    print("=" * 80)
    
    for filename in test_files:
        filepath = os.path.join(TEST_DATA_DIR, filename)
        
        print(f"\n{'=' * 80}")
        print(f"File: {filename}")
        print(f"Path: {filepath}")
        print(f"{'=' * 80}")
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            continue
        
        # Test detection
        print(f"\n🔍 Detecting bank...")
        detected_bank = detect_bank_from_pdf(filepath)
        print(f"\n✓ Detection result: {detected_bank}")
        print(f"{'=' * 80}")

def test_full_processing():
    """Test full processing with detected processor"""
    print("\n" + "=" * 80)
    print("TESTING FULL PROCESSING")
    print("=" * 80)
    
    # Import all processors
    from processors.bsi_processor import process_bsi_file
    from processors.mandiri_processor import process_mandiri_file
    from processors.mandiri_rk_processor import process_mandiri_rk_file
    from processors.bca_processor import process_bca_file
    from processors.bri_processor import process_bri_file
    from processors.bni_processor import process_bni_file
    from processors.bank_kalsel_processor import process_bank_kalsel_file
    
    processor_map = {
        'BSI': process_bsi_file,
        'MANDIRI': process_mandiri_file,
        'MANDIRI_RK': process_mandiri_rk_file,
        'BCA': process_bca_file,
        'BRI': process_bri_file,
        'BNI': process_bni_file,
        'BANK_KALSEL': process_bank_kalsel_file
    }
    
    for filename in test_files:
        filepath = os.path.join(TEST_DATA_DIR, filename)
        
        print(f"\n{'=' * 80}")
        print(f"Processing: {filename}")
        print(f"{'=' * 80}")
        
        if not os.path.exists(filepath):
            print(f"❌ File not found")
            continue
        
        try:
            # Detect bank
            detected_bank = detect_bank_from_pdf(filepath)
            print(f"✓ Detected bank: {detected_bank}")
            
            if detected_bank == 'UNKNOWN':
                print(f"⚠ Unknown bank, skipping processing")
                continue
            
            # Get processor
            processor = processor_map.get(detected_bank)
            if not processor:
                print(f"⚠ No processor found for {detected_bank}")
                continue
            
            # Process file
            print(f"\n📊 Processing with {detected_bank} processor...")
            df = processor(filepath, 'pdf')
            
            if df is None or len(df) == 0:
                print(f"❌ No data extracted")
                continue
            
            print(f"\n✓ SUCCESS! Extracted {len(df)} transactions")
            print(f"\nFirst 5 rows:")
            print(df.head().to_string())
            
            print(f"\nColumn names:")
            print(df.columns.tolist())
            
            print(f"\nData types:")
            print(df.dtypes)
            
            # Summary statistics
            if 'Type' in df.columns and 'Amount' in df.columns:
                print(f"\nTransaction summary:")
                print(f"  Total Debit: {len(df[df['Type'] == 'Debit'])} transactions")
                print(f"  Total Credit: {len(df[df['Type'] == 'Credit'])} transactions")
            
            # Save to CSV for inspection
            output_filename = f"test_output_{filename.replace('.pdf', '').replace(' ', '_')}.csv"
            output_path = os.path.join('outputs', output_filename)
            df.to_csv(output_path, index=False)
            print(f"\n💾 Saved to: {output_path}")
            
        except Exception as e:
            print(f"\n❌ ERROR during processing:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "🚀 " * 40)
    print("STARTING TEST FOR NEW RK FILES")
    print("🚀 " * 40 + "\n")
    
    # Test 1: Bank Detection
    test_bank_detection()
    
    # Test 2: Full Processing
    test_full_processing()
    
    print("\n" + "✅ " * 40)
    print("TEST COMPLETED")
    print("✅ " * 40 + "\n")
