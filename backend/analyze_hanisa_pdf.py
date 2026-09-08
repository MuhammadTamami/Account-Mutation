"""Analyze Hanisa PDF structure"""
import pdfplumber

pdf_path = r'uploads\HANISA JANUARI.pdf'

print("=" * 80)
print("Hanisa PDF Structure Analysis")
print("=" * 80)

with pdfplumber.open(pdf_path) as pdf:
    print(f"\nTotal pages: {len(pdf.pages)}")
    
    for page_num, page in enumerate(pdf.pages):
        print(f"\n{'='*80}")
        print(f"PAGE {page_num + 1}")
        print('='*80)
        
        text = page.extract_text()
        
        if text:
            lines = text.split('\n')
            print(f"Total lines: {len(lines)}")
            
            # Show first 50 lines
            print(f"\nFirst 50 lines:")
            for i, line in enumerate(lines[:50], 1):
                print(f"{i:3}. {line}")
            
            # Look for transaction patterns
            print(f"\n{'='*80}")
            print("Looking for date patterns (DD/MM/YY):")
            print('='*80)
            
            import re
            for i, line in enumerate(lines):
                if re.match(r'^\d{2}/\d{2}/\d{2}', line):
                    print(f"\nLine {i + 1}: {line}")
                    if i < len(lines) - 1:
                        print(f"Next: {lines[i + 1]}")
        else:
            print("  No text extracted from this page")
