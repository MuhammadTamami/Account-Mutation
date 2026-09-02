"""
Analyze new RK files to understand structure
"""

import pdfplumber
import os

TEST_DATA_DIR = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data'
test_files = [
    'RK PTBDK.pdf',
    'Rekening Koran BDK Jan - Juli 2026.pdf',
    'RK GIRO PTBDK.pdf'
]

def analyze_pdf(filepath, filename):
    """Extract and analyze PDF content"""
    print(f"\n{'=' * 80}")
    print(f"Analyzing: {filename}")
    print(f"{'=' * 80}")
    
    try:
        # Try with password
        passwords = ['', '07031985', '123456', '000000']
        pdf = None
        
        for pwd in passwords:
            try:
                pdf = pdfplumber.open(filepath, password=pwd)
                _ = len(pdf.pages)
                if pwd:
                    print(f"✓ PDF opened with password: {pwd}")
                else:
                    print(f"✓ PDF opened without password")
                break
            except Exception as e:
                if pdf:
                    pdf.close()
                pdf = None
                continue
        
        if not pdf:
            print(f"❌ Could not open PDF")
            return
        
        print(f"\nTotal pages: {len(pdf.pages)}")
        
        # Analyze first 3 pages
        for page_num in range(min(3, len(pdf.pages))):
            print(f"\n{'-' * 80}")
            print(f"PAGE {page_num + 1}")
            print(f"{'-' * 80}")
            
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text:
                lines = text.split('\n')
                print(f"Total lines: {len(lines)}")
                print(f"\nFirst 30 lines:")
                for i, line in enumerate(lines[:30], 1):
                    print(f"{i:3d}: {line}")
                
                # Try to extract tables
                print(f"\n{'-' * 40}")
                print(f"TABLES DETECTED:")
                print(f"{'-' * 40}")
                
                tables = page.extract_tables()
                if tables:
                    print(f"Found {len(tables)} tables")
                    for table_idx, table in enumerate(tables):
                        print(f"\nTable {table_idx + 1}:")
                        print(f"Rows: {len(table)}")
                        if table:
                            print(f"First 5 rows:")
                            for row_idx, row in enumerate(table[:5]):
                                print(f"  Row {row_idx + 1}: {row}")
                else:
                    print(f"No tables detected")
            else:
                print(f"⚠ No text extracted from page {page_num + 1}")
        
        pdf.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    for filename in test_files:
        filepath = os.path.join(TEST_DATA_DIR, filename)
        
        if os.path.exists(filepath):
            analyze_pdf(filepath, filename)
        else:
            print(f"\n❌ File not found: {filepath}")
    
    print(f"\n{'=' * 80}")
    print(f"ANALYSIS COMPLETED")
    print(f"{'=' * 80}")
