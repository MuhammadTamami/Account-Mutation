"""Debug BCA file that failed"""
import fitz  # PyMuPDF
import sys

pdf_path = r'uploads\ESTATEMENT-7326292057-052026-10-13-39.pdf'

print("=" * 80)
print("BCA File Debug Analysis")
print("=" * 80)

try:
    # Open PDF
    doc = fitz.open(pdf_path)
    print(f"\n✓ PDF opened successfully")
    print(f"  Total pages: {len(doc)}")
    
    # Extract text from first 3 pages
    for page_num in range(min(3, len(doc))):
        page = doc[page_num]
        text = page.get_text()
        
        print(f"\n{'='*80}")
        print(f"Page {page_num + 1} Text (first 1000 chars):")
        print('='*80)
        print(text[:1000])
        
        if len(text) < 100:
            print(f"\n⚠ WARNING: Page {page_num + 1} has very little text ({len(text)} chars)")
            print("This might be a scanned/image PDF that needs OCR")
    
    doc.close()
    
except Exception as e:
    print(f"\n❌ Error opening PDF: {e}")
    import traceback
    traceback.print_exc()
