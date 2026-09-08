"""Debug why Minimum Balance Fee line is not extracted"""
import pdfplumber
import re

pdf_path = r'uploads\HANISA JANUARI.pdf'

print("=" * 80)
print("Debug Hanisa Extraction")
print("=" * 80)

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    lines = text.split('\n')
    
    # Find the transaction lines
    target_line = None
    for i, line in enumerate(lines):
        if 'Minimum Balance Fee' in line:
            target_line = line
            print(f"\nFound target line {i + 1}: {line}")
            print(f"Length: {len(line)} chars")
            break
    
    if target_line:
        # Test datetime match
        datetime_match = re.match(r'^(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})', target_line)
        print(f"\nDatetime match: {datetime_match}")
        if datetime_match:
            print(f"  Date: {datetime_match.group(1)}")
            print(f"  Time: {datetime_match.group(2)}")
            
            # Extract rest of line
            rest_of_line = target_line[datetime_match.end():].strip()
            print(f"\nRest of line: '{rest_of_line}'")
            
            # Find numbers
            numbers = re.findall(r'[\d,]+\.[\d]{2}', rest_of_line)
            print(f"\nNumbers found: {numbers}")
            print(f"Count: {len(numbers)}")
            
            if len(numbers) >= 3:
                debit_str = numbers[-3]
                credit_str = numbers[-2]
                balance_str = numbers[-1]
                
                print(f"\nParsing:")
                print(f"  Debit:   {debit_str}")
                print(f"  Credit:  {credit_str}")
                print(f"  Balance: {balance_str}")
                
                # Check if debit > 0 and credit == 0
                def clean_amount(val):
                    return float(val.replace(',', ''))
                
                debit = clean_amount(debit_str)
                credit = clean_amount(credit_str)
                balance = clean_amount(balance_str)
                
                print(f"\nValues:")
                print(f"  Debit:   {debit}")
                print(f"  Credit:  {credit}")
                print(f"  Balance: {balance}")
                
                if debit > 0 and credit == 0:
                    print(f"\n✓ This is a DEBIT transaction!")
                elif credit > 0 and debit == 0:
                    print(f"\n✓ This is a CREDIT transaction!")
                else:
                    print(f"\n⚠ Ambiguous: both debit and credit have values or both zero")
            else:
                print(f"\n❌ Not enough numbers found (need 3)")
        else:
            print(f"\n❌ Datetime pattern does not match")
    else:
        print("\n❌ Target line not found!")
    
    # Now test the actual processor
    print(f"\n{'='*80}")
    print("Testing actual processor:")
    print('='*80)
    
    import sys
    sys.path.insert(0, 'processors')
    from bri_processor import process_bri_file
    
    df = process_bri_file(pdf_path, 'pdf')
    print(f"\nExtracted transactions: {len(df)}")
    for idx, row in df.iterrows():
        print(f"{row['Date']} | {row['Type']:6} | {row['Amount']:>15} | {row['Description'][:50]}")
