"""
Analyze CamScanner PDF files
"""
import pdfplumber
import os

TEST_DATA_DIR = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data'
test_files = [
    'Rekening Koran BDK Jan - Juli 2026.pdf',
    'Rekening koran bdk 2025.pdf'
]

def analyze_pdf_with_ocr(filepath, filename):
    """Analyze PDF and try OCR if needed"""
    print(f"\n{'=' * 80}")
    print(f"Analyzing: {filename}")
    print(f"{'=' * 80}")
    
    # Try pdfplumber first
    try:
        pdf = pdfplumber.open(filepath)
        print(f"✓ PDF opened: {len(pdf.pages)} pages")
        
        # Check first 2 pages
        for page_num in range(min(2, len(pdf.pages))):
            print(f"\n{'-' * 40}")
            print(f"PAGE {page_num + 1}")
            print(f"{'-' * 40}")
            
            page = pdf.pages[page_num]
            
            # Try text extraction
            text = page.extract_text()
            if text and len(text.strip()) > 50:
                print(f"✓ Text extracted: {len(text)} chars")
                lines = text.split('\n')[:10]
                print(f"First 10 lines:")
                for i, line in enumerate(lines, 1):
                    print(f"  {i}: {line}")
            else:
                print(f"⚠ Minimal or no text extracted")
                
                # Check if it has images (scanned)
                if page.images:
                    print(f"✓ Found {len(page.images)} images on page")
                    print(f"  -> This is likely a scanned/image-based PDF")
                    print(f"  -> OCR processing required")
                    
                    # Get page dimensions
                    print(f"\nPage info:")
                    print(f"  - Width: {page.width}")
                    print(f"  - Height: {page.height}")
                    
                    # Image info
                    for idx, img in enumerate(page.images[:2]):
                        print(f"\n  Image {idx + 1}:")
                        print(f"    - x0: {img.get('x0')}, y0: {img.get('y0')}")
                        print(f"    - x1: {img.get('x1')}, y1: {img.get('y1')}")
                        print(f"    - width: {img.get('width')}, height: {img.get('height')}")
                else:
                    print(f"⚠ No images found either")
                    print(f"  -> PDF might be corrupted or empty")
        
        pdf.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Try PyMuPDF as fallback
    print(f"\n{'-' * 40}")
    print(f"Trying PyMuPDF (fitz)...")
    print(f"{'-' * 40}")
    
    try:
        import fitz
        doc = fitz.open(filepath)
        print(f"✓ PyMuPDF opened: {len(doc)} pages")
        
        for page_num in range(min(2, len(doc))):
            page = doc[page_num]
            text = page.get_text()
            
            print(f"\nPage {page_num + 1}:")
            if text and len(text.strip()) > 50:
                print(f"  ✓ Text extracted: {len(text)} chars")
                lines = text.split('\n')[:5]
                for line in lines:
                    if line.strip():
                        print(f"    {line}")
            else:
                print(f"  ⚠ No text or minimal text")
                
                # Check for images
                img_list = page.get_images()
                if img_list:
                    print(f"  ✓ Found {len(img_list)} images")
                    print(f"  -> OCR processing will be needed")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ PyMuPDF error: {e}")

if __name__ == "__main__":
    for filename in test_files:
        filepath = os.path.join(TEST_DATA_DIR, filename)
        
        if os.path.exists(filepath):
            analyze_pdf_with_ocr(filepath, filename)
        else:
            print(f"\n❌ File not found: {filepath}")
    
    print(f"\n{'=' * 80}")
    print(f"ANALYSIS COMPLETED")
    print(f"{'=' * 80}")
