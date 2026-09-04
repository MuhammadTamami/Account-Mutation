"""
Mandiri Bank Statement Processor
Supports multiple PDF formats with password protection
"""
import pdfplumber
import pandas as pd
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert number format to float - supports both Indonesian and English formats"""
    if not amount_str or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip().replace('Rp', '').replace(' ', '').strip()
    
    # Handle different formats:
    # 1. Indonesian: 1.234.567,89 (dots for thousands, comma for decimal)
    # 2. International: 1,234,567.89 (commas for thousands, dot for decimal)
    # 3. Mixed/Raw: 200.000.000.00 (dots everywhere - need to detect decimal position)
    
    if ',' in amount_str and '.' in amount_str:
        # Both separators present
        last_comma_pos = amount_str.rfind(',')
        last_dot_pos = amount_str.rfind('.')
        
        if last_dot_pos > last_comma_pos:
            # Format: 1,234,567.89 (International)
            amount_str = amount_str.replace(',', '')
        else:
            # Format: 1.234.567,89 (Indonesian)
            amount_str = amount_str.replace('.', '').replace(',', '.')
    elif ',' in amount_str:
        # Only comma present
        last_comma_pos = amount_str.rfind(',')
        decimal_part_length = len(amount_str) - last_comma_pos - 1
        
        if decimal_part_length == 2:
            # Format: 1234567,89 or 1.234.567,89 (Indonesian decimal)
            amount_str = amount_str.replace(',', '.')
        else:
            # Format: 1,234,567 (thousand separator)
            amount_str = amount_str.replace(',', '')
    elif '.' in amount_str:
        # Only dots present - need to determine if last dot is decimal or thousand separator
        last_dot_pos = amount_str.rfind('.')
        decimal_part_length = len(amount_str) - last_dot_pos - 1
        
        if decimal_part_length == 2:
            # Format: 200.000.000.00 - last dot is decimal separator
            # Remove all dots except the last one
            amount_str = amount_str[:last_dot_pos].replace('.', '') + '.' + amount_str[last_dot_pos+1:]
        elif decimal_part_length > 3:
            # Format: 123456789.123456 (not a currency, keep as is)
            pass
        else:
            # Format: 1.234.567 (all are thousand separators, no decimal)
            amount_str = amount_str.replace('.', '')
    
    try:
        return float(amount_str)
    except Exception as e:
        print(f"⚠ Failed to parse amount '{amount_str}': {e}")
        return 0.0

def format_indonesian_number(value):
    """Format number as International format: 18,000,000.00 (comma for thousands, dot for decimal)"""
    if pd.isna(value) or value == 0:
        return "0.00"
    
    # Use standard US locale format
    formatted = f"{value:,.2f}"
    return formatted

def process_mandiri_pdf(filepath, pdf_password=''):
    """
    Process Mandiri bank statement PDF file
    Supports multiple Mandiri formats with password protection
    Auto-tries password "07031985" if PDF is password-protected
    """
    
    output_data = []
    summary_from_pdf = None
    account_info = None
    pdf = None
    
    # Try to open PDF with password
    passwords_to_try = []
    
    if pdf_password:
        passwords_to_try.append(pdf_password)
    
    # Always try the default password as fallback
    passwords_to_try.append('07031985')
    passwords_to_try.append('')  # Try without password last
    
    pdf_opened = False
    last_error = None
    
    for attempt_password in passwords_to_try:
        try:
            pdf = pdfplumber.open(filepath, password=attempt_password)
            # Try to access pages to verify password worked
            _ = len(pdf.pages)
            pdf_opened = True
            if attempt_password:
                print(f"✓ PDF opened with password")
            else:
                print(f"✓ PDF opened (no password required)")
            break
        except Exception as e:
            last_error = e
            if pdf:
                pdf.close()
            pdf = None
            # Try next password
            continue
    
    if not pdf_opened or pdf is None:
        error_msg = str(last_error) if last_error else "Unknown error"
        if 'password' in error_msg.lower():
            print(f"❌ PDF is password-protected and password is incorrect")
            raise Exception("PDF is password-protected. Please provide the correct password.")
        else:
            print(f"❌ Failed to open PDF: {error_msg}")
            raise Exception(f"Failed to open PDF: {error_msg}")
    
    try:
        print(f"📄 Processing Mandiri PDF: {len(pdf.pages)} pages")
        
        # Extract summary and account info from page 1
        if len(pdf.pages) > 0:
            summary_page = pdf.pages[0]
            summary_text = summary_page.extract_text()
            
            if summary_text:
                account_data = {}
                
                # Extract Account Number
                acc_no_match = re.search(r'Account No\..*?(\d{10,})', summary_text, re.DOTALL)
                if acc_no_match:
                    account_data['accountNumber'] = acc_no_match.group(1).strip()
                
                # Extract Account Name
                name_line_match = re.search(r'(\d{10,})\s+([A-Z\s]+?)\s+\2', summary_text)
                if name_line_match:
                    account_data['name'] = name_line_match.group(2).strip()
                else:
                    name_fallback = re.search(r'(\d{10,})\s+([A-Z][A-Z\s]+?)(?:\n|Period)', summary_text)
                    if name_fallback:
                        account_data['name'] = name_fallback.group(2).strip()
                
                # Extract Branch
                branch_match = re.search(r'Branch\s*\n?\s*([A-Z][A-Za-z\s]+?)(?:\n|Opening)', summary_text, re.MULTILINE)
                if branch_match:
                    account_data['branch'] = branch_match.group(1).strip()
                else:
                    branch_fallback = re.search(r'IDR\s+([A-Z][A-Za-z\s]+?)(?:\n|Opening)', summary_text)
                    if branch_fallback:
                        account_data['branch'] = branch_fallback.group(1).strip()
                
                if account_data:
                    account_info = account_data
                    print(f"✓ Account: {account_data.get('name', '?')} ({account_data.get('accountNumber', '?')})")
                
                # Extract Summary
                if 'Account Statement Summary' in summary_text:
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
            pending_reference = None
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines and headers
                if not line or 'Posting Date' in line or 'Account Statement' in line or 'Page' in line or 'Created' in line or 'Account No.' in line:
                    i += 1
                    continue
                
                # Check if this line is a reference number
                if re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', line) or (line.isdigit() and 8 <= len(line) <= 20):
                    pending_reference = line
                    i += 1
                    continue
                
                # FORMAT 1: DD/MM/YYYY HH:MM:SS (January/March format)
                date_time_match = re.match(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}):?(\d{2})?', line)
                
                if date_time_match:
                    try:
                        date_str = date_time_match.group(1)
                        time_str = date_time_match.group(2)
                        seconds = date_time_match.group(3) if date_time_match.group(3) else '00'
                        time_full = f"{time_str}:{seconds}"
                        
                        date = pd.to_datetime(date_str, format='%d/%m/%Y')
                        datetime_obj = pd.to_datetime(f"{date_str} {time_full}", format='%d/%m/%Y %H:%M:%S')
                        
                        rest_of_line = line[date_time_match.end():].strip()
                        
                        reference = pending_reference if pending_reference else '-'
                        pending_reference = None
                        
                        # Check if amounts are on the same line
                        numbers_same_line = re.findall(r'[\d,]+\.[\d]{2}', rest_of_line)
                        
                        if len(numbers_same_line) >= 3:
                            # All on same line
                            debit_str = numbers_same_line[-3]
                            credit_str = numbers_same_line[-2]
                            balance_str = numbers_same_line[-1]
                            
                            debit = clean_amount(debit_str)
                            credit = clean_amount(credit_str)
                            balance = clean_amount(balance_str)
                            
                            desc = rest_of_line
                            for num in numbers_same_line:
                                desc = desc.replace(num, '')
                            desc = desc.strip(' -')
                            desc = ' '.join(desc.split())
                            
                            if credit > 0 and debit == 0:
                                transaction_type = 'Credit'
                                amount = credit
                            elif debit > 0 and credit == 0:
                                transaction_type = 'Debit'
                                amount = debit
                            else:
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
                        
                        # EDGE CASE: Check PREVIOUS line for amounts (reverse order)
                        # This happens in page 5 where: "00 Bunga 03101 - 0.00 159,475.25 295,162,850.73" comes BEFORE "31/03/2026 23:59:"
                        if i > 0 and not rest_of_line:
                            prev_line = lines[i - 1].strip()
                            numbers_prev_line = re.findall(r'[\d,]+\.[\d]{2}', prev_line)
                            
                            if len(numbers_prev_line) >= 3:
                                debit_str = numbers_prev_line[-3]
                                credit_str = numbers_prev_line[-2]
                                balance_str = numbers_prev_line[-1]
                                
                                debit = clean_amount(debit_str)
                                credit = clean_amount(credit_str)
                                balance = clean_amount(balance_str)
                                
                                desc = prev_line
                                for num in numbers_prev_line:
                                    desc = desc.replace(num, '')
                                desc = desc.strip(' -')
                                desc = ' '.join(desc.split())
                                
                                if credit > 0 and debit == 0:
                                    transaction_type = 'Credit'
                                    amount = credit
                                elif debit > 0 and credit == 0:
                                    transaction_type = 'Debit'
                                    amount = debit
                                else:
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
                        
                        # Amounts on separate lines (normal order: date first, then amounts)
                        desc_from_date_line = rest_of_line
                        description_parts = [desc_from_date_line] if desc_from_date_line else []
                        found_transaction = False
                        
                        for j in range(i + 1, min(i + 15, len(lines))):
                            next_line = lines[j].strip()
                            
                            if not next_line:
                                continue
                            
                            if re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', next_line) or (next_line.isdigit() and 8 <= len(next_line) <= 20):
                                pending_reference = next_line
                                continue
                            
                            if re.match(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}', next_line):
                                break
                            
                            numbers = re.findall(r'[\d,]+\.[\d]{2}', next_line)
                            
                            if len(numbers) >= 3:
                                debit_str = numbers[-3]
                                credit_str = numbers[-2]
                                balance_str = numbers[-1]
                                
                                debit = clean_amount(debit_str)
                                credit = clean_amount(credit_str)
                                balance = clean_amount(balance_str)
                                
                                desc_from_amount_line = next_line
                                for num in numbers:
                                    desc_from_amount_line = desc_from_amount_line.replace(num, '')
                                desc_from_amount_line = desc_from_amount_line.strip(' -')
                                
                                if desc_from_amount_line:
                                    description_parts.insert(0, desc_from_amount_line)
                                
                                description = ' '.join(description_parts).strip()
                                description = ' '.join(description.split())
                                
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
                                i = j + 1
                                break
                            else:
                                if not (re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', next_line) or (next_line.isdigit() and 8 <= len(next_line) <= 20)):
                                    description_parts.append(next_line)
                        
                        if not found_transaction:
                            i += 1
                        
                    except Exception as e:
                        print(f"⚠ Error parsing line {i}: {e}")
                        i += 1
                        continue
                
                # FORMAT 2: DD Mon YYYY, (February format - with comma)
                elif re.match(r'(\d{2}\s+[A-Za-z]{3}\s+\d{4}),', line):
                    try:
                        date_match = re.match(r'(\d{2}\s+[A-Za-z]{3}\s+\d{4}),', line)
                        date_str = date_match.group(1)
                        
                        date = pd.to_datetime(date_str, format='%d %b %Y')
                        
                        reference = pending_reference if pending_reference else '-'
                        pending_reference = None
                        
                        found_transaction = False
                        
                        for j in range(i + 1, min(i + 5, len(lines))):
                            next_line = lines[j].strip()
                            
                            if not next_line:
                                continue
                            
                            if re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', next_line) or (next_line.isdigit() and 8 <= len(next_line) <= 20):
                                pending_reference = next_line
                                continue
                            
                            if re.match(r'\d{2}\s+[A-Za-z]{3}\s+\d{4},', next_line) or re.match(r'\d{2}/\d{2}/\d{4}', next_line):
                                break
                            
                            numbers = re.findall(r'[\d,]+\.[\d]{2}', next_line)
                            
                            if len(numbers) >= 3:
                                debit_str = numbers[-3]
                                credit_str = numbers[-2]
                                balance_str = numbers[-1]
                                
                                debit = clean_amount(debit_str)
                                credit = clean_amount(credit_str)
                                balance = clean_amount(balance_str)
                                
                                time_str = None
                                description_parts = []
                                
                                for k in range(j + 1, min(j + 10, len(lines))):
                                    desc_line = lines[k].strip()
                                    
                                    if not desc_line:
                                        continue
                                    
                                    if re.match(r'^\d{8}[A-Z]{6,8}\d{3}[A-Z]?\d{0,10}$', desc_line) or (desc_line.isdigit() and 8 <= len(desc_line) <= 20):
                                        pending_reference = desc_line
                                        break
                                    
                                    if re.match(r'\d{2}\s+[A-Za-z]{3}\s+\d{4},', desc_line) or re.match(r'\d{2}/\d{2}/\d{4}', desc_line):
                                        break
                                    
                                    time_match = re.match(r'^(\d{2}:\d{2}:\d{2})', desc_line)
                                    if time_match and not time_str:
                                        time_str = time_match.group(1)
                                        desc_after_time = desc_line[time_match.end():].strip()
                                        if desc_after_time:
                                            description_parts.append(desc_after_time)
                                    else:
                                        description_parts.append(desc_line)
                                    
                                    if time_str and len(description_parts) >= 2:
                                        break
                                
                                description = ' '.join(description_parts).strip()
                                description = ' '.join(description.split())
                                
                                if time_str:
                                    try:
                                        datetime_obj = pd.to_datetime(f"{date_str} {time_str}", format='%d %b %Y %H:%M:%S')
                                    except:
                                        datetime_obj = date
                                else:
                                    datetime_obj = date
                                
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
                        print(f"⚠ Error parsing line {i}: {e}")
                        i += 1
                        continue
                
                # FORMAT 3: DD Mon YYYY (no comma) - e-Statement format
                # The structure varies:
                # Case A: "04 Jan 2026 Transfer dari BANK MANDIRI" (date + desc on same line)
                #         "12 +304.000,00 21.955.379,96" (row number + amounts)
                #         "13:36:38 WIB OKTAFIYA ..." (time + more desc)
                # Case B: "Transfer dari BANK MANDIRI" (desc first)
                #         "05 Jan 2026" (date on next line)
                #         "15 AHMAD RIFANI ... +65.000,00 23.605.379,96" (row + desc + amounts)
                #         "09:41:45 WIB" (time)
                elif re.search(r'\d{2}\s+[A-Za-z]{3}\s+\d{4}', line):
                    try:
                        # Extract date from line
                        date_match = re.search(r'(\d{2}\s+[A-Za-z]{3}\s+\d{4})', line)
                        date_str = date_match.group(1)
                        date = pd.to_datetime(date_str, format='%d %b %Y')
                        
                        reference = pending_reference if pending_reference else '-'
                        pending_reference = None
                        
                        # Get description from same line (after date)
                        desc_on_date_line = line[date_match.end():].strip()
                        description_parts = []
                        if desc_on_date_line and not desc_on_date_line.isdigit():
                            description_parts.append(desc_on_date_line)
                        
                        # Also check if there's description BEFORE the date
                        desc_before_date = line[:date_match.start()].strip()
                        if desc_before_date and not desc_before_date.isdigit():
                            description_parts.insert(0, desc_before_date)
                        
                        time_str = None
                        found_transaction = False
                        
                        # Look for amounts and time in following lines
                        for j in range(i + 1, min(i + 15, len(lines))):
                            next_line = lines[j].strip()
                            
                            if not next_line:
                                continue
                            
                            # Stop if we hit another date
                            if re.search(r'\d{2}\s+[A-Za-z]{3}\s+\d{4}', next_line):
                                break
                            
                            # Skip header/footer lines
                            if any(skip in next_line for skip in ['No Date', 'No Tanggal', 'Bank Mandiri', 'dari', 'of', 'Mandiri Call', 'berizin']):
                                continue
                            
                            # Look for time pattern
                            time_match = re.search(r'(\d{2}:\d{2}:\d{2})\s+WI[BT]', next_line)
                            if time_match:
                                time_str = time_match.group(1)
                                # Extract any description after time
                                desc_after_time = next_line[time_match.end():].strip()
                                # Remove reference number if present
                                desc_after_time = re.sub(r'\d{10,}', '', desc_after_time).strip()
                                if desc_after_time:
                                    description_parts.append(desc_after_time)
                            
                            # Look for amounts pattern: [+/-]number,number balance
                            # Pattern: optional row number, optional desc, +/-amount, balance
                            amounts_match = re.search(r'([+-][\d.]+,\d{2})\s+([\d.]+,\d{2})$', next_line)
                            
                            if amounts_match:
                                amount_str = amounts_match.group(1)
                                balance_str = amounts_match.group(2)
                                
                                # Extract description from this line (before amounts)
                                desc_part = next_line[:amounts_match.start()].strip()
                                # Remove row number (1-3 digits at start)
                                desc_part = re.sub(r'^\d{1,3}\s+', '', desc_part)
                                # Remove reference numbers (long numeric)
                                desc_part = re.sub(r'\d{10,}', '', desc_part).strip()
                                if desc_part:
                                    description_parts.append(desc_part)
                                
                                # Build final description
                                description = ' '.join(description_parts).strip()
                                description = ' '.join(description.split())
                                
                                # Determine transaction type
                                if amount_str.startswith('+'):
                                    transaction_type = 'Credit'
                                    amount = clean_amount(amount_str[1:])
                                elif amount_str.startswith('-'):
                                    transaction_type = 'Debit'
                                    amount = clean_amount(amount_str[1:])
                                else:
                                    i = j + 1
                                    found_transaction = True
                                    break
                                
                                balance = clean_amount(balance_str)
                                
                                # Create datetime
                                if time_str:
                                    datetime_obj = pd.to_datetime(f"{date_str} {time_str}", format='%d %b %Y %H:%M:%S')
                                else:
                                    datetime_obj = date
                                
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
                                # This line is description (no amounts yet)
                                # Skip row numbers and long reference numbers
                                if next_line.isdigit() and len(next_line) <= 3:
                                    continue
                                desc_clean = re.sub(r'\d{10,}', '', next_line).strip()
                                if desc_clean and not time_match:  # Don't duplicate time line
                                    description_parts.append(desc_clean)
                        
                        if not found_transaction:
                            i += 1
                    
                    except Exception as e:
                        print(f"⚠ Error parsing line {i}: {e}")
                        i += 1
                        continue
                else:
                    i += 1
        
        print(f"✓ Extracted {len(output_data)} transactions from Mandiri PDF")
        
        if len(output_data) == 0:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(output_data)
        df = df.sort_values(['DateTime', 'OriginalIndex']).reset_index(drop=True)
        df = df.drop(columns=['DateTime', 'OriginalIndex'])
        
        # Attach metadata
        if summary_from_pdf:
            df.attrs['pdf_summary'] = summary_from_pdf
        if account_info:
            df.attrs['account_info'] = account_info
        
        return df
        
    except Exception as e:
        print(f"❌ Error processing Mandiri PDF: {e}")
        raise
    finally:
        if pdf:
            pdf.close()

def process_mandiri_csv(filepath):
    """Process Mandiri CSV - not implemented yet"""
    return pd.DataFrame()

def process_mandiri_excel(filepath):
    """Process Mandiri Excel - not implemented yet"""
    return pd.DataFrame()

def process_mandiri_file(filepath, file_ext, pdf_password=''):
    """Main entry point"""
    if file_ext == 'csv':
        return process_mandiri_csv(filepath)
    elif file_ext == 'pdf':
        return process_mandiri_pdf(filepath, pdf_password)
    elif file_ext in ['xlsx', 'xls']:
        return process_mandiri_excel(filepath)
    else:
        return pd.DataFrame()
