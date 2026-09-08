"""Check BRI PDF raw text for fee-related entries"""
import pdfplumber

pdf_path = r'uploads\1. 184399112771_e-StatementBRImo_018001000731560_Jan2026_20260728_110025.pdf'

print("=" * 80)
print("BRI PDF Raw Text - Looking for Fees")
print("=" * 80)

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Look for fee-related keywords
            if any(keyword in line_lower for keyword in ['fee', 'monthly', 'admin', 'biaya admin', 'biaya bulanan', 'charge']):
                print(f"\n[Page {page_num + 1}, Line {i + 1}]")
                print(f"  Current: {line}")
                if i > 0:
                    print(f"  Before:  {lines[i-1]}")
                if i < len(lines) - 1:
                    print(f"  After:   {lines[i+1]}")

print(f"\n{'='*80}")
print("Done")
