"""
Mandiri Rekening Koran (RK) Processor
Untuk format standard Mandiri RK seperti format BDK
Format: DATE | EFF. DATE | DESCRIPTION | TRANS CODE | CHEQUE NO | Debit | Kredit | Ledger Balance
"""
import pdfplumber
import pandas as pd
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert number with comma separator to float"""
    if not amount_str or amount_str == '.00' or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip().replace('Rp', '').strip()
    # Remove comma thousand separators and convert to float
    # Format: 1,234,567.89 -> 1234567.89
    amount_str = amount_str.replace(',', '')
    
    try:
        return float(amount_str)
    except:
        return 0.0

def format_indonesian_number(value):
    """Format number as Indonesian format (comma as decimal separator, dot as thousand separator)
    BUT for compatibility with app.py, we use comma for both thousand and decimal
    Output format: 1.234.567,89
    """
    if pd.isna(value) or value == 0:
        return "0,00"
    
    # Format: 1234567.89 -> 1.234.567,89
    formatted = f"{value:.2f}"
    parts = formatted.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    # Add thousand separators (dot) - but app.py expects comma, so let's not use separator
    # Just use plain number with comma decimal for compatibility
    # Format: 1234567,89
    return f"{integer_part},{decimal_part}"

def parse_mandiri_rk_line(line):
    """
    Parse a transaction line from Mandiri RK format
    Handles two formats:
    Format 1: DD/MM/YY DD/MM/YY DESCRIPTION CODE DEBIT CREDIT BALANCE Cr/Dr (with 2 dates)
    Format 2: DD/MM/YY DESCRIPTION CODE DEBIT CREDIT BALANCE Cr/Dr (with 1 date only)
    
    Example Format 1: 31/01/25 31/01/25 Biaya Administrasi 0000/453 12,500.00 .00 3,291,581.25 Cr
    Example Format 2: 31/01/25 Pajak 0000/198 2,822.39 .00 5,057,640.43 Cr
    """
    line = line.strip()
    
    # Skip header, empty lines, or B/F lines
    if not line or 'B/F' in line or 'TRANS EFF' in line or 'DATE' in line:
        return None
    
    # Match the pattern: DATE [DATE] DESCRIPTION CODE DEBIT CREDIT BALANCE Cr/Dr
    # Dates: DD/MM/YY format
    # Code: XXXX/XXX format
    # Amounts: can be .00 or actual numbers with commas
    
    # Try to find date pattern at start
    date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})', line)
    if not date_match:
        return None
    
    trans_date_str = date_match.group(1)
    
    # Parse date (handle 2-digit year)
    try:
        trans_date = pd.to_datetime(trans_date_str, format='%d/%m/%y')
    except:
        try:
            trans_date = pd.to_datetime(trans_date_str, format='%d/%m/%Y')
        except:
            return None
    
    # Remove the first date from line
    rest = line[len(trans_date_str):].strip()
    
    # Check if there's a second date (optional)
    second_date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})', rest)
    if second_date_match:
        # Remove second date too
        rest = rest[len(second_date_match.group(1)):].strip()
    
    # Now rest should be: DESCRIPTION CODE DEBIT CREDIT BALANCE Cr/Dr
    # Find code pattern: XXXX/XXX
    code_match = re.search(r'(\d{4}/\d{3})', rest)
    code = code_match.group(1) if code_match else '0000/000'
    
    # Find all numbers (including .00)
    # Pattern: optional digits, comma-separated digits, mandatory dot with 2 decimals
    # This will match: .00, 1.00, 1,234.56, etc.
    numbers = re.findall(r'(?:[\d,]+)?\.[\d]{2}', rest)
    
    if len(numbers) < 3:
        # Need at least debit, credit, balance
        return None
    
    # Last 3 numbers are: debit, credit, balance
    debit_str = numbers[-3]
    credit_str = numbers[-2]
    balance_str = numbers[-1]
    
    # Parse amounts
    debit = clean_amount(debit_str)
    credit = clean_amount(credit_str)
    balance = clean_amount(balance_str)
    
    # Determine transaction type
    if credit > 0 and debit == 0:
        transaction_type = 'Credit'
        amount = credit
    elif debit > 0 and credit == 0:
        transaction_type = 'Debit'
        amount = debit
    else:
        # Both have values or both zero - skip
        return None
    
    # Extract description (everything before code, after dates)
    description = rest
    if code_match:
        # Get everything before code
        code_pos = rest.find(code)
        description = rest[:code_pos].strip()
    
    # Clean description - remove numbers
    for num in numbers:
        description = description.replace(num, '')
    description = description.strip()
    
    # Find balance type (Cr or Dr) 
    balance_type = 'Cr'
    if 'Dr' in line:
        balance_type = 'Dr'
    
    return {
        'Date': trans_date,
        'Reference': code,
        'Description': description,
        'Type': transaction_type,
        'Amount': format_indonesian_number(amount),
        'Balance': format_indonesian_number(balance),
        'BalanceType': balance_type
    }

def process_mandiri_rk_pdf(filepath, pdf_password=''):
    """
    Process Mandiri Rekening Koran (RK) format PDF
    Standard format with columns: DATE | EFF. DATE | DESCRIPTION | TRANS CODE | Debit | Kredit | Balance
    """
    
    output_data = []
    pdf = None
    account_info = None
    opening_balance = None
    opening_date = None
    sequence_number = 0  # To maintain order of transactions on same date
    
    # Try passwords
    passwords_to_try = []
    if pdf_password:
        passwords_to_try.append(pdf_password)
    passwords_to_try.extend(['07031985', ''])
    
    pdf_opened = False
    for pwd in passwords_to_try:
        try:
            pdf = pdfplumber.open(filepath, password=pwd)
            _ = len(pdf.pages)
            pdf_opened = True
            if pwd:
                print(f"✓ PDF opened with password")
            else:
                print(f"✓ PDF opened without password")
            break
        except:
            if pdf:
                pdf.close()
            pdf = None
            continue
    
    if not pdf_opened or pdf is None:
        raise Exception("Failed to open PDF. Password may be required.")
    
    try:
        print(f"📄 Processing Mandiri RK PDF: {len(pdf.pages)} pages")
        
        # Extract account info from first page
        if len(pdf.pages) > 0:
            first_page = pdf.pages[0]
            first_text = first_page.extract_text()
            
            if first_text:
                lines = first_text.split('\n')
                # Look for account info in first few lines
                for i, line in enumerate(lines[:25]):
                    # Look for account number pattern: XXXX-XX-XX-XXXXXX-X
                    acc_match = re.search(r'(\d{8}-\d{2}-\d{2}-\d{6}-\d)', line)
                    if acc_match:
                        account_info = {
                            'accountNumber': acc_match.group(1),
                            'name': lines[i-1].strip() if i > 0 else 'Unknown'
                        }
                        # Look for branch
                        for j in range(max(0, i-3), min(len(lines), i+2)):
                            if 'Branch:' in lines[j] or 'branch' in lines[j].lower():
                                branch_match = re.search(r'Branch:(\d+)', lines[j])
                                if branch_match:
                                    account_info['branch'] = branch_match.group(1)
                
                # Look for B/F (Brought Forward) - opening balance (separate loop)
                for i, line in enumerate(lines[:25]):
                    bf_match = re.search(r'B/F\s+([\d,\.]+)\s+(Cr|Dr)', line)
                    if bf_match:
                        opening_balance = clean_amount(bf_match.group(1))
                        balance_type = bf_match.group(2)
                        # Try to get date from Period line
                        for prev_line in lines[:i]:
                            period_match = re.search(r'Period\s*:\s*(\d{1,2}/\d{1,2}/\d{2,4})', prev_line)
                            if period_match:
                                try:
                                    opening_date = pd.to_datetime(period_match.group(1), format='%d/%m/%y')
                                except:
                                    try:
                                        opening_date = pd.to_datetime(period_match.group(1), format='%d/%m/%Y')
                                    except:
                                        pass
                                break
                        print(f"✓ Opening Balance (B/F): {format_indonesian_number(opening_balance)} {balance_type}")
                        break
        
        # Process all pages
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            if not text:
                print(f"⚠ Page {page_num + 1}: No text extracted")
                continue
            
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                
                # Skip header and empty lines
                if not line or 'DATE PRINTED' in line or 'TRANS EFF.' in line or 'Branch:' in line:
                    continue
                
                # Skip B/F line (already captured)
                if line.startswith('B/F'):
                    continue
                
                # Skip page headers
                if 'DATE' in line and 'DESCRIPTION' in line:
                    continue
                
                # Try to parse transaction line
                transaction = parse_mandiri_rk_line(line)
                
                if transaction:
                    sequence_number += 1
                    transaction['Sequence'] = sequence_number
                    output_data.append(transaction)
        
        print(f"✓ Extracted {len(output_data)} transactions from Mandiri RK")
        
        if len(output_data) == 0 and opening_balance is None:
            print(f"⚠ No transactions found in PDF")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(output_data)
        
        # Note: B/F (Brought Forward) is detected but NOT added as a separate entry
        # The first actual transaction already reflects the B/F balance
        # This matches the original PDF format where B/F is just a reference line
        
        # Sort by Sequence to maintain original order from PDF (important for same-date transactions)
        if 'Sequence' in df.columns:
            df = df.sort_values('Sequence').reset_index(drop=True)
            # Remove Sequence column after sorting
            df = df.drop('Sequence', axis=1)
        else:
            # Fallback: sort by date only
            df = df.sort_values('Date').reset_index(drop=True)
        
        # Add account info if available
        if account_info:
            df.attrs['account_info'] = account_info
            print(f"✓ Account: {account_info.get('name', '?')} - {account_info.get('accountNumber', '?')}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error processing Mandiri RK PDF: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        if pdf:
            pdf.close()

def process_mandiri_rk_file(filepath, file_ext, pdf_password=''):
    """
    Main entry point for Mandiri RK processor
    Currently only supports PDF format
    """
    if file_ext == 'pdf':
        return process_mandiri_rk_pdf(filepath, pdf_password)
    else:
        raise Exception(f"Mandiri RK processor only supports PDF format, got: {file_ext}")
