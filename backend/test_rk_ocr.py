"""
Test OCR processing for scanned RK BDK files
"""
import os
import sys

# File paths
TEST_DATA_DIR = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data'
test_files = [
    'Rekening Koran BDK Jan - Juli 2026.pdf',
    'Rekening koran bdk 2025.pdf'
]

def check_dependencies():
    """Check if required dependencies are installed"""
    print("=" * 80)
    print("CHECKING DEPENDENCIES")
    print("=" * 80)
    
    all_ok = True
    
    # Check pytesseract
    try:
        import pytesseract
        print("✓ pytesseract installed")
        
        # Try to get tesseract version
        try:
            version = pytesseract.get_tesseract_version()
            print(f"  Version: {version}")
        except:
            print("  ⚠ Tesseract OCR engine not found!")
            print("  Please install from: https://github.com/UB-Mannheim/tesseract/wiki")
            all_ok = False
    except ImportError:
        print("❌ pytesseract not installed")
        print("  Install with: pip install pytesseract")
        all_ok = False
    
    # Check PyMuPDF
    try:
        import fitz
        print("✓ PyMuPDF installed")
    except ImportError:
        print("❌ PyMuPDF not installed")
        print("  Install with: pip install PyMuPDF")
        all_ok = False
    
    # Check PIL
    try:
        from PIL import Image
        print("✓ Pillow (PIL) installed")
    except ImportError:
        print("❌ Pillow not installed")
        print("  Install with: pip install Pillow")
        all_ok = False
    
    print("=" * 80)
    return all_ok

def test_ocr_detection():
    """Test bank detection for OCR files"""
    from processors.bank_detector import detect_bank_from_pdf
    
    print("\n" + "=" * 80)
    print("TESTING BANK DETECTION FOR SCANNED FILES")
    print("=" * 80)
    
    for filename in test_files:
        filepath = os.path.join(TEST_DATA_DIR, filename)
        
        print(f"\n{'=' * 80}")
        print(f"File: {filename}")
        print(f"{'=' * 80}")
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            continue
        
        # Test detection
        print(f"\n🔍 Detecting bank...")
        detected_bank = detect_bank_from_pdf(filepath)
        print(f"\n✓ Detection result: {detected_bank}")

def test_ocr_processing():
    """Test OCR processing"""
    from processors.mandiri_rk_ocr_processor import process_mandiri_rk_ocr_file
    
    print("\n" + "=" * 80)
    print("TESTING OCR PROCESSING")
    print("=" * 80)
    
    for filename in test_files:
        filepath = os.path.join(TEST_DATA_DIR, filename)
        
        print(f"\n{'=' * 80}")
        print(f"Processing: {filename}")
        print(f"{'=' * 80}")
        
        if not os.path.exists(filepath):
            print(f"❌ File not found")
            continue
        
        try:
            # Process file with OCR
            df = process_mandiri_rk_ocr_file(filepath, 'pdf')
            
            if df is None or len(df) == 0:
                print(f"\n❌ No data extracted")
                continue
            
            print(f"\n✅ SUCCESS! Extracted {len(df)} transactions")
            
            print(f"\nFirst 5 rows:")
            print(df.head().to_string())
            
            print(f"\nColumn names:")
            print(df.columns.tolist())
            
            # Summary statistics
            if 'Type' in df.columns:
                print(f"\nTransaction summary:")
                print(f"  Total Debit: {len(df[df['Type'] == 'Debit'])} transactions")
                print(f"  Total Credit: {len(df[df['Type'] == 'Credit'])} transactions")
            
            # Save to CSV
            output_filename = f"test_output_OCR_{filename.replace('.pdf', '').replace(' ', '_')}.csv"
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
    print("STARTING OCR TEST FOR SCANNED RK FILES")
    print("🚀 " * 40 + "\n")
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Missing dependencies! Please install required packages.")
        print("\nTo install:")
        print("  pip install pytesseract PyMuPDF Pillow")
        print("\nAlso install Tesseract OCR:")
        print("  https://github.com/UB-Mannheim/tesseract/wiki")
        sys.exit(1)
    
    # Test 1: Bank Detection
    test_ocr_detection()
    
    # Test 2: OCR Processing
    print("\n" + "⏳ " * 40)
    print("STARTING OCR PROCESSING (This may take a while...)")
    print("⏳ " * 40)
    
    test_ocr_processing()
    
    print("\n" + "✅ " * 40)
    print("OCR TEST COMPLETED")
    print("✅ " * 40 + "\n")
