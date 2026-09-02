"""
Quick OCR test - simplified version
Tests if OCR is working on scanned RK files
"""
import os

def test_dependencies():
    """Quick dependency check"""
    print("\n" + "=" * 60)
    print("CHECKING OCR DEPENDENCIES")
    print("=" * 60 + "\n")
    
    # Check pytesseract
    try:
        import pytesseract
        print("✓ pytesseract: Installed")
        
        # Set tesseract path for Windows if not in PATH
        import platform
        if platform.system() == 'Windows':
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"  Set path: {path}")
                    break
    except ImportError:
        print("❌ pytesseract: NOT installed")
        print("   Fix: pip install pytesseract")
        return False
    
    # Check PyMuPDF
    try:
        import fitz
        print("✓ PyMuPDF: Installed")
    except ImportError:
        print("❌ PyMuPDF: NOT installed")
        print("   Fix: pip install PyMuPDF")
        return False
    
    # Check PIL
    try:
        from PIL import Image
        print("✓ Pillow: Installed")
    except ImportError:
        print("❌ Pillow: NOT installed")
        print("   Fix: pip install Pillow")
        return False
    
    # Check Tesseract engine
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract OCR Engine: v{version}")
        return True
    except:
        print("❌ Tesseract OCR Engine: NOT installed")
        print("\n   Download from:")
        print("   https://github.com/UB-Mannheim/tesseract/wiki")
        print("\n   Windows installer:")
        print("   https://digi.bib.uni-mannheim.de/tesseract/")
        print("\n   After installation, add to PATH:")
        print("   C:\\Program Files\\Tesseract-OCR")
        return False

def simple_ocr_test():
    """Simple OCR test without full processing"""
    print("\n" + "=" * 60)
    print("SIMPLE OCR TEST")
    print("=" * 60 + "\n")
    
    try:
        from processors.mandiri_rk_ocr_processor import extract_images_from_pdf, ocr_image
        
        # Test file
        test_file = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\Rekening koran bdk 2025.pdf'
        
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            return False
        
        print(f"Testing: Rekening koran bdk 2025.pdf")
        print(f"Extracting images...")
        
        # Extract first page image
        images = extract_images_from_pdf(test_file)
        
        if not images:
            print("❌ No images extracted")
            return False
        
        print(f"✓ Extracted {len(images)} page(s)")
        
        # OCR first page only
        first_img = images[0]['image']
        print(f"\nPerforming OCR on first page...")
        print(f"Image size: {first_img.size}")
        
        text = ocr_image(first_img)
        
        if not text or len(text.strip()) < 50:
            print(f"❌ OCR failed or minimal text extracted")
            return False
        
        print(f"\n✓ OCR SUCCESS!")
        print(f"Extracted {len(text)} characters")
        print(f"\nFirst 500 characters:")
        print("-" * 60)
        print(text[:500])
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "🔍 " * 30)
    print("QUICK OCR TEST")
    print("🔍 " * 30)
    
    # Step 1: Check dependencies
    if not test_dependencies():
        print("\n" + "=" * 60)
        print("❌ MISSING DEPENDENCIES")
        print("=" * 60)
        print("\nPlease install missing dependencies first.")
        print("\nQuick install:")
        print("  pip install pytesseract PyMuPDF Pillow")
        print("\nThen install Tesseract OCR engine:")
        print("  https://github.com/UB-Mannheim/tesseract/wiki")
        input("\nPress Enter to exit...")
        exit(1)
    
    # Step 2: Simple OCR test
    print("\n")
    if simple_ocr_test():
        print("\n" + "=" * 60)
        print("✅ OCR TEST PASSED")
        print("=" * 60)
        print("\nOCR is working correctly!")
        print("You can now process scanned PDF files.")
    else:
        print("\n" + "=" * 60)
        print("❌ OCR TEST FAILED")
        print("=" * 60)
        print("\nPlease check the error messages above.")
    
    input("\nPress Enter to exit...")
