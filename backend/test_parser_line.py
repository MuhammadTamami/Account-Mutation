# -*- coding: utf-8 -*-
"""
Test parser on specific lines from RK GIRO
"""
import re
import pandas as pd

def clean_amount(amount_str):
    """Convert number with comma separator to float"""
    if not amount_str or amount_str == '.00' or amount_str == '-':
        return 0.0
    amount_str = str(amount_str).strip().replace('Rp', '').strip()
    amount_str = amount_str.replace(',', '')
    try:
        return float(amount_str)
    except:
        return 0.0

def format_indonesian_number(value):
    """Format number"""
    if pd.isna(value) or value == 0:
        return "0,00"
    formatted = f"{value:.2f}"
    parts = formatted.split('.')
    return f"{parts[0]},{parts[1]}"

# Test lines from RK GIRO January
test_lines = [
    "14/01/25 14/01/25 M39CLU/I/25/PBK MNUAL SBUM 1U 0000/005 .00 4,000,000.00 5,046,350.86 Cr",  # Format 1: 2 dates
    "31/01/25 31/01/25 Bunga Rekening 0000/160 .00 14,111.96 5,060,462.82 Cr",  # Format 1: 2 dates
    "31/01/25 Pajak 0000/198 2,822.39 .00 5,057,640.43 Cr",  # Format 2: 1 date
    "31/01/25 Biaya Administrasi 0000/453 25,000.00 .00 5,032,640.43 Cr",  # Format 2: 1 date
    "31/01/25 PCKPR_K_KOMP 8070/001 .00 168,680,000.00 173,712,640.43 Cr",  # Format 2: 1 date
    "31/01/25 PCKPR_K_KOMP 8067/001 .00 170,680,000.00 344,392,640.43 Cr",  # Format 2: 1 date
    "31/01/25 PCKPR_K_KOMP 8086/001 .00 170,680,000.00 515,072,640.43 Cr",  # Format 2: 1 date
]

print("Testing parser on RK GIRO lines:\n")
print("=" * 80)

for i, line in enumerate(test_lines, 1):
    print(f"\nLine {i}:")
    print(f"Input: {line}")
    
    # Try to parse
    # Find first date
    date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})', line)
    if not date_match:
        print("  X No date found")
        continue
    
    trans_date_str = date_match.group(1)
    print(f"  Date found: {trans_date_str}")
    
    # Parse date
    try:
        trans_date = pd.to_datetime(trans_date_str, format='%d/%m/%y')
        print(f"  Parsed date: {trans_date.strftime('%Y-%m-%d')}")
    except:
        print(f"  X Failed to parse date")
        continue
    
    # Remove first date
    rest = line[len(trans_date_str):].strip()
    print(f"  After removing 1st date: {rest[:60]}...")
    
    # Check for second date
    second_date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})', rest)
    if second_date_match:
        rest = rest[len(second_date_match.group(1)):].strip()
        print(f"  After removing 2nd date: {rest[:60]}...")
    
    # Find code
    code_match = re.search(r'(\d{4}/\d{3})', rest)
    code = code_match.group(1) if code_match else '0000/000'
    print(f"  Code: {code}")
    
    # Find numbers
    numbers = re.findall(r'(?:[\d,]+)?\.[\d]{2}', rest)
    print(f"  Numbers found: {numbers}")
    
    if len(numbers) >= 3:
        debit_str = numbers[-3]
        credit_str = numbers[-2]
        balance_str = numbers[-1]
        
        debit = clean_amount(debit_str)
        credit = clean_amount(credit_str)
        balance = clean_amount(balance_str)
        
        print(f"  Debit: {debit}, Credit: {credit}, Balance: {balance}")
        
        if credit > 0 and debit == 0:
            txn_type = 'Credit'
            amount = credit
        elif debit > 0 and credit == 0:
            txn_type = 'Debit'
            amount = debit
        else:
            print(f"  X Both zero or both have values")
            continue
        
        # Description
        description = rest
        if code_match:
            code_pos = rest.find(code)
            description = rest[:code_pos].strip()
        for num in numbers:
            description = description.replace(num, '')
        description = description.strip()
        
        print(f"  OK SUCCESS!")
        print(f"    Type: {txn_type}")
        print(f"    Amount: {format_indonesian_number(amount)}")
        print(f"    Balance: {format_indonesian_number(balance)}")
        print(f"    Description: {description}")
    else:
        print(f"  X Not enough numbers ({len(numbers)} < 3)")

print("\n" + "=" * 80)
