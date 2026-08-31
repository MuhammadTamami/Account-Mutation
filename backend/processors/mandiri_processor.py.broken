import pdfplumber
import pandas as pd
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert number format to float - supports both Indonesian and English formats"""
    if not amount_str or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip()
    
    # Remove currency symbols and spaces
    amount_str = amount_str.replace('Rp', '').strip()
    
    # Detect format by looking at the last 3 characters
    # English format: "9,755,500.00" - dot before last 2 digits
    # Indonesian format: "9.755.500,00" - comma before last 2 digits
    
    if ',' in amount_str and '.' in amount_str:
        # Both present - check which comes last
        last_comma_pos = amount_str.rfind(',')
        last_dot_pos = amount_str.rfind('.')
        
        if last_dot_pos > last_comma_pos:
            # English format: 1,234,567.89
            # Remove commas (thousand separator), keep dot (decimal)
            amount_str = amount_str.replace(',', '')
        else:
            # Indonesian format: 1.234.567,89
            # Remove dots (thousand separator), replace comma with dot
            amount_str = amount_str.replace('.', '').replace(',', '.')
    elif ',' in amount_str:
        # Only comma - could be Indonesian decimal or English thousand separator
        # If comma is in last 3 chars, it's decimal (Indonesian)
        # Otherwise, it's thousand separator (English)
        last_comma_pos = amount_str.rfind(',')
        if len(amount_str) - last_comma_pos <= 3:
            # Indonesian decimal: 1234,56
            amount_str = amount_str.replace(',', '.')
        else:
            # English thousand: 1,234
            amount_str = amount_str.replace(',', '')
    elif '.' in amount_str:
        # Only dot - could be Indonesian thousand or English decimal
        # If dot is in last 3 chars, it's decimal (English)
        # Otherwise, it's thousand separator (Indonesian)
        last_dot_pos = amount_str.rfind('.')
        if len(amount_str) - last_dot_pos > 3:
            # Indonesian thousand: 1.234
            amount_str = amount_str.replace('.', '')
    
    try:
        return float(amount_str)
    except:
        return 0.0

def format_indonesian_number(value):
    """Format number as Indonesian format: 1,499,754,00 (comma as decimal separator)"""
    if pd.isna(value) or value == 0:
        return "0,00"
    
    # Split into integer and decimal parts
    formatted = f"{value:.2f}"
    parts = formatted.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    # Add thousand separators (keep as comma for thousands)
    integer_with_sep = f"{int(integer_part):,}"
    
    # Replace dot with comma for decimal separator
    return f"{integer_with_sep},{decimal_part}"

def parse_mandiri_date(date_str):
    """Parse various Mandiri date formats"""
    try:
        # Common formats: DD/MM/YYYY, DD-MM-YYYY, etc.
        for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y']:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except:
                continue
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

def extract_table_from_pdf(filepath):
    """Extract transaction table from Mandiri PDF statement"""
    
    transactions = []
    
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            # Extract text
            text = page.extract_text()
            
            if not text:
                continue
            
            # Split by lines
            lines = text.split('\n')
            
            # Look for transaction patterns
            # Mandiri format typically: Date | Description | Debit | Credit | Balance
            for line in lines:
                # Skip header and summary lines
                if any(keyword in line.lower() for keyword in ['tanggal', 'saldo', 'total', 'mutasi']):
                    continue
                
                # Try to match transaction pattern
                # Pattern: date at start, numbers at end
                parts = line.split()
                
                if len(parts) < 3:
                    continue
                
                # Try to find date pattern (DD/MM/YYYY or similar)
                date_match = re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', line)
                
                if date_match:
                    date_str = date_match.group()
                    
                    # Extract numbers (potential amounts)
                    numbers = re.findall(r'[\d,.]+', line.replace(date_str, ''))
                    
                    if len(numbers) >= 2:
                        # Extract description (between date and numbers)
                        desc_start = line.find(date_str) + len(date_str)
                        desc_end = line.rfind(numbers[-2]) if len(numbers) > 1 else line.rfind(numbers[-1])
                        description = line[desc_start:desc_end].strip()
                        
                        transactions.append({
                            'date': date_str,
                            'description': description,
                            'numbers': numbers
                        })
    
    return transactions

def process_mandiri_pdf(filepath, pdf_password=''):
    """
    Process Mandiri bank statement PDF file
    Supports multiple Mandiri formats with variations
    Supports password-protected PDFs
    """
    
    output_data = []
    summary_from_pdf = None
    account_info = None
    
    try:
        # Try to open PDF with password if provided
        try:
            with pdfplumber.open(filepath, password=pdf_password) as pdf:
                print(f"📄 Processing Mandiri PDF: {len(pdf.pages)} pages")
                
                # First, try to extract summary and account info from page 1
                if len(pdf.pages) > 0:
                    summary_page = pdf.pages[0]
                    summary_text = summary_page.extract_text()
                    
                    # Extract Account Information
                if summary_text:
                    account_data = {}
                    
                    # Extract Account Number (after "Account No.")
                    acc_no_match = re.search(r'Account No\..*?(\d{10,})', summary_text, re.DOTALL)
                    if acc_no_match:
                        account_data['accountNumber'] = acc_no_match.group(1).strip()
                    
                    # Extract Account Name
                    name_line_match = re.search(r'(\d{10,})\s+([A-Z\s]+?)\s+\2', summary_text)
                    if name_line_match:
                        account_data['name'] = name_line_match.group(2).strip()
                    else:
                        # Fallback: Try to get name after account number
                        name_fallback = re.search(r'(\d{10,})\s+([A-Z][A-Z\s]+?)(?:\n|Period)', summary_text)
                        if name_fallback:
                            account_data['name'] = name_fallback.group(2).strip()
                    
                    # Extract Branch (after "Branch")
                    branch_match = re.search(r'Branch\s*\n?\s*([A-Z][A-Za-z\s]+?)(?:\n|Opening)', summary_text, re.MULTILINE)
                    if branch_match:
                        account_data['branch'] = branch_match.group(1).strip()
                    else:
                        # Fallback: try different pattern
                        branch_fallback = re.search(r'IDR\s+([A-Z][A-Za-z\s]+?)(?:\n|Opening)', summary_text)
                        if branch_fallback:
                            account_data['branch'] = branch_fallback.group(1).strip()
                    
                    if account_data:
                        account_info = account_data
                        print(f"✓ Account: {account_data.get('name', '?')} ({account_data.get('accountNumber', '?')})")
                
                # Extract Summary
                if summary_text and 'Account Statement Summary' in summary_text:
                    lines = summary_text.split('\n')
                    summary_data = {
                        'no_of_debit': None,
                        'no_of_credit': None,
                        'total_amount_debited': None,
                        'total_amount_credited': None
                    }
                    
                    full_text = ' '.join(lines)
                    
                    opening_match = re.search(r'Opening\s+Balance\s+No\.\s+of\s+Debit\s+Total\s+Amount\s+Debited\s+([\d,]+\.[\d]{2})\s+(\d+)\s+([\d,]+\.[\d]{2})', full_text)
                    if opening_match:
                        summary_data['no_of_debit'] = int(opening_match.group(2))
                        summary_data['total_amount_debited'] = clean_amount(opening_match.group(3))
                    
                    closing_match = re.search(r'Closing\s+Balance\s+No\.\s+of\s+Credit\s+Total\s+Amount\s+Credited\s+([\d,]+\.[\d]{2})\s+(\d+)\s+([\d,]+\.[\d]{2})', full_text)
                    if closing_match:
                        summary_data['no_of_credit'] = int(closing_match.group(2))
                        summary_data['total_amount_credited'] = clean_amount(closing_match.group(3))
                    
                    if all(v is not None for v in summary_data.values()):
                        summary_from_pdf = summary_data
                        print(f"✓ Summary: {summary_data['no_of_debit']} debit, {summary_data['no_of_credit']} credit")
                
                    # Process ALL pages for transactions
                    for page_num, page in enumerate(pdf.pages):
                        text = page.extract_text()
                    
                    if not text:
                        continue
                
                    lines = text.split('\n')
                
                    i = 0
                    pending_reference = None  # Store reference number if it appears before date
                
                    while i < len(lines):
                        line = lines[i].strip()
                    
                        # Skip empty lines, headers, and footers
                        if not line or 'Posting Date' in line or 'Account Statement' in line or 'Page' in line or 'Created' in line or 'Account No.' in line:
                            i += 1
                            continue
                    
                        # Check if this line is a reference number (appears before transaction)
                        # Format: 20260102BRINIDJA010O0293531079 or 20260202BRINIDJA010O02
                        # Also accept all-numeric references: 15479199, 5221845039305685
                        if re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', line) or (line.isdigit() and 8 <= len(line) <= 20):
                            pending_reference = line
                            i += 1
                            continue
                    
                        # DATE FORMAT 1: DD/MM/YYYY HH:MM:SS (January/March format)
                        # Examples: 
                        # "02/01/2026 08:18:49 BRINIDJA/PANSYAH - 0.00 112,500,000.00 141,069,453.68"
                        # "02/03/2026 08:57: description..."
                        date_time_match = re.match(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}):?(\d{2})?', line)
                    
                        if date_time_match:
                            try:
                                date_str = date_time_match.group(1)
                                time_str = date_time_match.group(2)
                                seconds = date_time_match.group(3) if date_time_match.group(3) else '00'
                                time_full = f"{time_str}:{seconds}"
                            
                                # Parse date
                                date = pd.to_datetime(date_str, format='%d/%m/%Y')
                                datetime_obj = pd.to_datetime(f"{date_str} {time_full}", format='%d/%m/%Y %H:%M:%S')
                            
                                # Extract rest of line after datetime
                                rest_of_line = line[date_time_match.end():].strip()
                            
                                # Use pending reference if available
                                reference = pending_reference if pending_reference else '-'
                                pending_reference = None  # Reset
                            
                                # CHECK IF AMOUNTS ARE ON THE SAME LINE (Format 1)
                                # Look for 3 numbers in the same line
                                numbers_same_line = re.findall(r'[\d,]+\.[\d]{2}', rest_of_line)
                            
                                if len(numbers_same_line) >= 3:
                                    # Format 1: All on same line!
                                    # Example: "BRINIDJA/PANSYAH - 0.00 112,500,000.00 141,069,453.68"
                                
                                    debit_str = numbers_same_line[-3]
                                    credit_str = numbers_same_line[-2]
                                    balance_str = numbers_same_line[-1]
                                
                                    debit = clean_amount(debit_str)
                                    credit = clean_amount(credit_str)
                                    balance = clean_amount(balance_str)
                                
                                    # Extract description (before the amounts)
                                    desc = rest_of_line
                                    for num in numbers_same_line:
                                        desc = desc.replace(num, '')
                                    desc = desc.strip(' -')
                                    desc = ' '.join(desc.split())  # Clean up spaces
                                
                                    # Determine transaction type
                                    if credit > 0 and debit == 0:
                                        transaction_type = 'Credit'
                                        amount = credit
                                    elif debit > 0 and credit == 0:
                                        transaction_type = 'Debit'
                                        amount = debit
                                    else:
                                        # Skip if both are zero or both have values
                                        i += 1
                                        continue
                                
                                    output_data.append({
                                        'DateTime': datetime_obj,
                                        'OriginalIndex': len(output_data),
                                        'Date': date,
                                        'Reference': reference,
                                        'Description': desc,
                                        'Type': transaction_type,
                                        'Amount': format_indonesian_number(amount),
                                        'Balance': format_indonesian_number(balance)
                                    })
                                
                                    i += 1
                                    continue
                            
                                # FORMAT 2: Amounts on separate lines
                                # Collect description from this line
                                desc_from_date_line = rest_of_line
                            
                                # Collect all description lines until we find the amounts line
                                description_parts = [desc_from_date_line] if desc_from_date_line else []
                                found_transaction = False
                            
                                for j in range(i + 1, min(i + 15, len(lines))):
                                    next_line = lines[j].strip()
                                
                                    # Skip empty lines
                                    if not next_line:
                                        continue
                                
                                    # Check if this is a reference number (store for next transaction)
                                    if re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', next_line) or (next_line.isdigit() and 8 <= len(next_line) <= 20):
                                        pending_reference = next_line
                                        continue
                                
                                    # Stop if we hit another date
                                    if re.match(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}', next_line):
                                        break
                                
                                    # Check if this line has transaction amounts
                                    numbers = re.findall(r'[\d,]+\.[\d]{2}', next_line)
                                
                                    if len(numbers) >= 3:
                                        # This is the amounts line!
                                        debit_str = numbers[-3]
                                        credit_str = numbers[-2]
                                        balance_str = numbers[-1]
                                    
                                        debit = clean_amount(debit_str)
                                        credit = clean_amount(credit_str)
                                        balance = clean_amount(balance_str)
                                    
                                        # Extract description from this line (before amounts)
                                        desc_from_amount_line = next_line
                                        for num in numbers:
                                            desc_from_amount_line = desc_from_amount_line.replace(num, '')
                                        desc_from_amount_line = desc_from_amount_line.strip(' -')
                                    
                                        if desc_from_amount_line:
                                            description_parts.insert(0, desc_from_amount_line)
                                    
                                        # Build full description
                                        description = ' '.join(description_parts).strip()
                                        description = ' '.join(description.split())
                                    
                                        # Determine transaction type
                                        if credit > 0 and debit == 0:
                                            transaction_type = 'Credit'
                                            amount = credit
                                        elif debit > 0 and credit == 0:
                                            transaction_type = 'Debit'
                                            amount = debit
                                        else:
                                            # Skip if both are zero or both have values
                                            i = j + 1
                                            found_transaction = True
                                            break
                                    
                                        output_data.append({
                                            'DateTime': datetime_obj,
                                            'OriginalIndex': len(output_data),
                                            'Date': date,
                                            'Reference': reference,
                                            'Description': description,
                                            'Type': transaction_type,
                                            'Amount': format_indonesian_number(amount),
                                            'Balance': format_indonesian_number(balance)
                                        })
                                    
                                        found_transaction = True
                                        i = j + 1
                                        break
                                    else:
                                        # This is a description continuation line
                                        if not (re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', next_line) or (next_line.isdigit() and 8 <= len(next_line) <= 20)):
                                            description_parts.append(next_line)
                            
                                if not found_transaction:
                                    i += 1
                            
                            except Exception as e:
                                print(f"⚠ Error parsing line {i}: {e}")
                                i += 1
                                continue
                    
                        # DATE FORMAT 2: DD Mon YYYY, (February format)
                        # Example: "02 Feb 2026, 15479199" or "02 Feb 2026,"
                        elif re.match(r'(\d{2}\s+[A-Za-z]{3}\s+\d{4}),', line):
                            try:
                                # Extract date
                                date_match = re.match(r'(\d{2}\s+[A-Za-z]{3}\s+\d{4}),', line)
                                date_str = date_match.group(1)
                            
                                # Parse date (format: DD Mon YYYY)
                                date = pd.to_datetime(date_str, format='%d %b %Y')
                            
                                # Use pending reference if available
                                reference = pending_reference if pending_reference else '-'
                                pending_reference = None
                            
                                # Look for amounts in next line
                                # Format: "- 0.00 112,500,000.00 388,767,415.08"
                                found_transaction = False
                            
                                for j in range(i + 1, min(i + 5, len(lines))):
                                    next_line = lines[j].strip()
                                
                                    if not next_line:
                                        continue
                                
                                    # Check if this is a reference (skip it)
                                    if re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', next_line) or (next_line.isdigit() and 8 <= len(next_line) <= 20):
                                        pending_reference = next_line
                                        continue
                                
                                    # Stop if we hit another date
                                    if re.match(r'\d{2}\s+[A-Za-z]{3}\s+\d{4},', next_line) or re.match(r'\d{2}/\d{2}/\d{4}', next_line):
                                        break
                                
                                    # Look for amounts line
                                    numbers = re.findall(r'[\d,]+\.[\d]{2}', next_line)
                                
                                    if len(numbers) >= 3:
                                        # Found amounts!
                                        debit_str = numbers[-3]
                                        credit_str = numbers[-2]
                                        balance_str = numbers[-1]
                                    
                                        debit = clean_amount(debit_str)
                                        credit = clean_amount(credit_str)
                                        balance = clean_amount(balance_str)
                                    
                                        # Look for time and description in following lines
                                        time_str = None
                                        description_parts = []
                                    
                                        for k in range(j + 1, min(j + 10, len(lines))):
                                            desc_line = lines[k].strip()
                                        
                                            if not desc_line:
                                                continue
                                        
                                            # Check if next line is reference (stop here)
                                            if re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', desc_line) or (desc_line.isdigit() and 8 <= len(desc_line) <= 20):
                                                pending_reference = desc_line
                                                break
                                        
                                            # Stop if we hit another date
                                            if re.match(r'\d{2}\s+[A-Za-z]{3}\s+\d{4},', desc_line) or re.match(r'\d{2}/\d{2}/\d{4}', desc_line):
                                                break
                                        
                                            # Try to extract time (HH:MM:SS)
                                            time_match = re.match(r'^(\d{2}:\d{2}:\d{2})', desc_line)
                                            if time_match and not time_str:
                                                time_str = time_match.group(1)
                                                # Rest of line after time is description
                                                desc_after_time = desc_line[time_match.end():].strip()
                                                if desc_after_time:
                                                    description_parts.append(desc_after_time)
                                            else:
                                                # This is description
                                                description_parts.append(desc_line)
                                        
                                            # Stop collecting if we have time and some description
                                            if time_str and len(description_parts) >= 2:
                                                break
                                    
                                        # Build description
                                        description = ' '.join(description_parts).strip()
                                        description = ' '.join(description.split())  # Clean spaces
                                    
                                        # Create datetime
                                        if time_str:
                                            try:
                                                datetime_obj = pd.to_datetime(f"{date_str} {time_str}", format='%d %b %Y %H:%M:%S')
                                            except:
                                                datetime_obj = date
                                        else:
                                            datetime_obj = date
                                    
                                        # Determine transaction type
                                        if credit > 0 and debit == 0:
                                            transaction_type = 'Credit'
                                            amount = credit
                                        elif debit > 0 and credit == 0:
                                            transaction_type = 'Debit'
                                            amount = debit
                                        else:
                                            i = j + 1
                                            found_transaction = True
                                            break
                                    
                                        output_data.append({
                                            'DateTime': datetime_obj,
                                            'OriginalIndex': len(output_data),
                                            'Date': date,
                                            'Reference': reference,
                                            'Description': description,
                                            'Type': transaction_type,
                                            'Amount': format_indonesian_number(amount),
                                            'Balance': format_indonesian_number(balance)
                                        })
                                    
                                        found_transaction = True
                                        i = k if 'k' in locals() else j + 1
                                        break
                            
                                if not found_transaction:
                                    i += 1
                        
                            except Exception as e:
                                print(f"⚠ Error parsing Feb format line {i}: {e}")
                                i += 1
                                continue
                        else:
                            i += 1
        except Exception as password_error:
            # Check if it's a password error
            if 'PDFPasswordIncorrect' in str(type(password_error).__name__) or 'password' in str(password_error).lower():
                print(f"🔒 PDF is password protected")
                raise Exception('PDF_PASSWORD_REQUIRED')
            else:
                # Re-raise other errors
                raise
    
    except Exception as e:
        # Check for password error
        if 'PDF_PASSWORD_REQUIRED' in str(e):
            print(f"❌ PDF requires password")
            raise Exception('PDF file is password protected. Please provide the correct password.')
        
        print(f"❌ Error processing Mandiri PDF: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    
    # Create DataFrame
    if not output_data:
        print(f"⚠ No transactions found in PDF")
        return pd.DataFrame()
    
    print(f"✓ Extracted {len(output_data)} transactions")
    
    result_df = pd.DataFrame(output_data)
    
    # Sort by DateTime first, then by OriginalIndex
    result_df = result_df.sort_values(['DateTime', 'OriginalIndex']).reset_index(drop=True)
    
    # Drop helper columns
    result_df = result_df.drop(columns=['DateTime', 'OriginalIndex'])
    
    # Attach summary data as metadata
    if summary_from_pdf:
        result_df.attrs['pdf_summary'] = summary_from_pdf
    
    # Attach account info as metadata
    if account_info:
        result_df.attrs['account_info'] = account_info
    
    return result_df


def process_mandiri_csv(filepath):
    """Process Mandiri CSV format"""
    try:
        # Try different separators
        for sep in [',', ';', '\t']:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, sep=sep, encoding=encoding)
                    if len(df.columns) > 3:
                        break
                except:
                    continue
        
        output_data = []
        
        for idx, row in df.iterrows():
            # Skip header rows
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).lower() in ['posting', 'date', 'tanggal']:
                continue
            
            try:
                # Find date column
                date = None
                for col in df.columns:
                    if any(keyword in str(col).lower() for keyword in ['posting', 'date', 'tanggal', 'tgl']):
                        try:
                            # Try various date formats
                            date_str = str(row[col])
                            date = pd.to_datetime(date_str, format='%d %b %Y')
                        except:
                            try:
                                date = pd.to_datetime(date_str)
                            except:
                                pass
                        break
                
                if not date or pd.isna(date):
                    continue
                
                # Find description
                description = ''
                for col in df.columns:
                    if any(keyword in str(col).lower() for keyword in ['description', 'keterangan', 'deskripsi']):
                        description = str(row[col])
                        break
                
                # Find amounts
                debit = 0
                credit = 0
                balance = 0
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'debit' in col_lower or 'db' in col_lower:
                        debit = clean_amount(row[col])
                    elif 'credit' in col_lower or 'cr' in col_lower or 'kredit' in col_lower:
                        credit = clean_amount(row[col])
                    elif 'balance' in col_lower or 'saldo' in col_lower:
                        balance = clean_amount(row[col])
                
                # Determine type
                if credit > 0:
                    transaction_type = 'Credit'
                    amount = credit
                elif debit > 0:
                    transaction_type = 'Debit'
                    amount = debit
                else:
                    continue
                
                output_data.append({
                    'Date': date,
                    'Reference': '-',
                    'Description': description,
                    'Type': transaction_type,
                    'Amount': format_indonesian_number(amount),
                    'Balance': format_indonesian_number(balance)
                })
            
            except Exception as e:
                continue
        
        return pd.DataFrame(output_data)
    
    except Exception as e:
        print(f"Error processing Mandiri CSV: {e}")
        return pd.DataFrame()

def process_mandiri_excel(filepath):
    """Process Mandiri Excel format"""
    try:
        # Read Excel file
        df = pd.read_excel(filepath)
        
        output_data = []
        
        for idx, row in df.iterrows():
            # Skip header rows
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).lower() in ['posting', 'date', 'tanggal']:
                continue
            
            try:
                # Find date column
                date = None
                for col in df.columns:
                    if any(keyword in str(col).lower() for keyword in ['posting', 'date', 'tanggal', 'tgl']):
                        try:
                            date_str = str(row[col])
                            date = pd.to_datetime(date_str, format='%d %b %Y')
                        except:
                            try:
                                date = pd.to_datetime(date_str)
                            except:
                                pass
                        break
                
                if not date or pd.isna(date):
                    continue
                
                # Find description
                description = ''
                for col in df.columns:
                    if any(keyword in str(col).lower() for keyword in ['description', 'keterangan', 'deskripsi']):
                        description = str(row[col])
                        break
                
                # Find amounts
                debit = 0
                credit = 0
                balance = 0
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'debit' in col_lower or 'db' in col_lower:
                        debit = clean_amount(row[col])
                    elif 'credit' in col_lower or 'cr' in col_lower or 'kredit' in col_lower:
                        credit = clean_amount(row[col])
                    elif 'balance' in col_lower or 'saldo' in col_lower:
                        balance = clean_amount(row[col])
                
                # Determine type
                if credit > 0:
                    transaction_type = 'Credit'
                    amount = credit
                elif debit > 0:
                    transaction_type = 'Debit'
                    amount = debit
                else:
                    continue
                
                output_data.append({
                    'Date': date,
                    'Reference': '-',
                    'Description': description,
                    'Type': transaction_type,
                    'Amount': format_indonesian_number(amount),
                    'Balance': format_indonesian_number(balance)
                })
            
            except Exception as e:
                continue
        
        return pd.DataFrame(output_data)
    
    except Exception as e:
        print(f"Error processing Mandiri Excel: {e}")
        return pd.DataFrame()

def process_mandiri_file(filepath, file_ext, pdf_password=''):
    """
    Main entry point for Mandiri processor
    Auto-detects format (CSV, PDF, Excel)
    """
    if file_ext == 'csv':
        return process_mandiri_csv(filepath)
    elif file_ext == 'pdf':
        return process_mandiri_pdf(filepath, pdf_password)
    elif file_ext in ['xlsx', 'xls']:
        return process_mandiri_excel(filepath)
    else:
        return pd.DataFrame()
