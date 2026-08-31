"""
BNI Bank Statement Processor
Supports CSV, PDF, and Excel formats
"""
import pandas as pd
import pdfplumber
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert number format to float - English format (comma=thousands, dot=decimal)"""
    if pd.isna(amount_str) or amount_str == '' or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip()
    amount_str = amount_str.replace('Rp', '').replace('IDR', '').strip()
    
    # BNI uses English format: 20,000,000.00 (comma=thousands, dot=decimal)
    amount_str = amount_str.replace(',', '')  # Remove thousand separators
    
    try:
        return float(amount_str)
    except:
        return 0.0

def format_indonesian_number(value):
    """Format number as Indonesian format"""
    if pd.isna(value) or value == 0:
        return "0,00"
    
    formatted = f"{value:.2f}"
    parts = formatted.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    integer_with_sep = f"{int(integer_part):,}"
    return f"{integer_with_sep},{decimal_part}"

def parse_bni_date(date_str):
    """Parse BNI date formats"""
    try:
        for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y', '%Y-%m-%d', '%d.%m.%Y']:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except:
                continue
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

def process_bni_csv(filepath):
    """Process BNI CSV format"""
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
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).lower() in ['tanggal', 'date', 'tgl']:
                continue
            
            try:
                # Find date column
                date = None
                for col in df.columns:
                    if any(keyword in str(col).lower() for keyword in ['tanggal', 'date', 'tgl']):
                        date = parse_bni_date(str(row[col]))
                        break
                
                if not date or pd.isna(date):
                    continue
                
                # Find description
                description = ''
                for col in df.columns:
                    if any(keyword in str(col).lower() for keyword in ['keterangan', 'description', 'deskripsi', 'uraian', 'remarks']):
                        description = str(row[col])
                        break
                
                # Find amounts
                debit = 0
                credit = 0
                balance = 0
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'debet' in col_lower or 'debit' in col_lower or col_lower == 'db':
                        debit = clean_amount(row[col])
                    elif 'kredit' in col_lower or 'credit' in col_lower or col_lower == 'cr':
                        credit = clean_amount(row[col])
                    elif 'mutasi' in col_lower:
                        mutasi = clean_amount(row[col])
                        if mutasi > 0:
                            credit = mutasi
                        else:
                            debit = abs(mutasi)
                    elif 'saldo' in col_lower or 'balance' in col_lower:
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
        print(f"Error processing BNI CSV: {e}")
        return pd.DataFrame()

def process_bni_pdf(filepath):
    """
    Process BNI TRANSACTION INQUIRY PDF
    
    Format:
    - Header: Account, Period, Beginning Balance, Total Debit, Total Credit
    - Table columns: No., Post Date, Branch, Journal No., Description, Amount, Db/Cr, Balance
    - Date format: DD/MM/YYYY HH.MM.SS
    """
    
    output_data = []
    account_info = {}
    summary_from_pdf = {}
    
    try:
        with pdfplumber.open(filepath) as pdf:
            print(f"📄 Processing BNI PDF: {len(pdf.pages)} pages")
            
            # Extract account info and summary from first page
            if len(pdf.pages) > 0:
                first_text = pdf.pages[0].extract_text()
                
                if first_text:
                    # Extract account number and name
                    # Format: "Account : 1710194229 / KALTRABU INDAH PT ( )"
                    acc_match = re.search(r'Account\s*:\s*(\d+)\s*/\s*(.+?)(?:\(|$)', first_text)
                    if acc_match:
                        account_info['accountNumber'] = acc_match.group(1).strip()
                        account_info['name'] = acc_match.group(2).strip()
                    
                    # Extract period
                    period_match = re.search(r'Period\s*:\s*(.+)', first_text)
                    if period_match:
                        account_info['period'] = period_match.group(1).strip()
                    
                    # Extract summary
                    beginning_match = re.search(r'Beginning Balance\s*:\s*([\d,\.]+)', first_text)
                    if beginning_match:
                        summary_from_pdf['beginning_balance'] = clean_amount(beginning_match.group(1))
                    
                    total_debit_match = re.search(r'Total Debit\s*:\s*([\d,\.]+)', first_text)
                    if total_debit_match:
                        summary_from_pdf['total_amount_debited'] = clean_amount(total_debit_match.group(1))
                    
                    total_credit_match = re.search(r'Total Credit\s*:\s*([\d,\.]+)', first_text)
                    if total_credit_match:
                        summary_from_pdf['total_amount_credited'] = clean_amount(total_credit_match.group(1))
                    
                    if account_info:
                        print(f"✓ Account: {account_info.get('name', '?')} ({account_info.get('accountNumber', '?')})")
                    if summary_from_pdf:
                        debit_amt = summary_from_pdf.get('total_amount_debited', 0)
                        credit_amt = summary_from_pdf.get('total_amount_credited', 0)
                        print(f"✓ Summary: Debit={debit_amt:,.0f}, Credit={credit_amt:,.0f}")
            
            # Process all pages
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                
                if not text:
                    continue
                
                lines = text.split('\n')
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Skip empty lines and headers
                    if not line or 'Post Date' in line or 'TRANSACTION INQUIRY' in line or 'Account Information' in line:
                        i += 1
                        continue
                    
                    # Check if line starts with transaction number pattern
                    # Format: "1 02/01/2024 INTERNET 978570 TRANSFER DARI | ..."
                    trans_match = re.match(r'^(\d+)\s+(\d{2}/\d{2}/\d{4})\s+(.+)', line)
                    
                    if trans_match:
                        try:
                            trans_no = trans_match.group(1)
                            date_str = trans_match.group(2)
                            rest = trans_match.group(3).strip()
                            
                            date = pd.to_datetime(date_str, format='%d/%m/%Y')
                            
                            # Extract time if present (format: HH.MM.SS)
                            time_match = re.search(r'(\d{2}\.\d{2}\.\d{2})', rest)
                            time_str = time_match.group(1) if time_match else None
                            
                            # Look for amounts at end of line
                            # Pattern: amount Db/Cr balance
                            # Example: "20,000,000.00 C 8,761,834,229.00"
                            amounts_match = re.search(r'([\d,\.]+)\s+([CD])\s+([\d,\.]+)$', line)
                            
                            if amounts_match:
                                # Transaction complete on same line
                                amount_str = amounts_match.group(1)
                                db_cr = amounts_match.group(2)
                                balance_str = amounts_match.group(3)
                                
                                amount = clean_amount(amount_str)
                                balance = clean_amount(balance_str)
                                
                                # Extract description (everything after date/time, before amounts)
                                desc_text = rest
                                if time_match:
                                    desc_text = rest[time_match.end():].strip()
                                
                                # Remove amounts from description
                                desc_end_pos = desc_text.rfind(amount_str)
                                if desc_end_pos > 0:
                                    description = desc_text[:desc_end_pos].strip()
                                else:
                                    description = desc_text
                                
                                # Clean up description
                                description = ' '.join(description.split())
                                
                                transaction_type = 'Credit' if db_cr == 'C' else 'Debit'
                                
                                # Create datetime
                                if time_str:
                                    time_formatted = time_str.replace('.', ':')
                                    datetime_obj = pd.to_datetime(f"{date_str} {time_formatted}", format='%d/%m/%Y %H:%M:%S')
                                else:
                                    datetime_obj = date
                                
                                output_data.append({
                                    'DateTime': datetime_obj,
                                    'Date': date,
                                    'Reference': trans_no,
                                    'Description': description,
                                    'Type': transaction_type,
                                    'Amount': format_indonesian_number(amount),
                                    'Balance': format_indonesian_number(balance)
                                })
                                
                                i += 1
                            else:
                                # Description continues on next lines, amounts on separate line
                                description_parts = [rest]
                                if time_match:
                                    desc_after_time = rest[time_match.end():].strip()
                                    description_parts = [desc_after_time] if desc_after_time else []
                                
                                found_amounts = False
                                
                                for j in range(i + 1, min(i + 10, len(lines))):
                                    next_line = lines[j].strip()
                                    
                                    if not next_line:
                                        continue
                                    
                                    # Stop if we hit another transaction
                                    if re.match(r'^\d+\s+\d{2}/\d{2}/\d{4}', next_line):
                                        break
                                    
                                    # Look for amounts
                                    amounts_match = re.search(r'([\d,\.]+)\s+([CD])\s+([\d,\.]+)$', next_line)
                                    
                                    if amounts_match:
                                        amount_str = amounts_match.group(1)
                                        db_cr = amounts_match.group(2)
                                        balance_str = amounts_match.group(3)
                                        
                                        amount = clean_amount(amount_str)
                                        balance = clean_amount(balance_str)
                                        
                                        # Extract description before amounts
                                        desc_before_amount = next_line[:next_line.rfind(amount_str)].strip()
                                        if desc_before_amount:
                                            description_parts.append(desc_before_amount)
                                        
                                        description = ' '.join(description_parts).strip()
                                        description = ' '.join(description.split())
                                        
                                        transaction_type = 'Credit' if db_cr == 'C' else 'Debit'
                                        
                                        # Create datetime
                                        if time_str:
                                            time_formatted = time_str.replace('.', ':')
                                            datetime_obj = pd.to_datetime(f"{date_str} {time_formatted}", format='%d/%m/%Y %H:%M:%S')
                                        else:
                                            datetime_obj = date
                                        
                                        output_data.append({
                                            'DateTime': datetime_obj,
                                            'Date': date,
                                            'Reference': trans_no,
                                            'Description': description,
                                            'Type': transaction_type,
                                            'Amount': format_indonesian_number(amount),
                                            'Balance': format_indonesian_number(balance)
                                        })
                                        
                                        found_amounts = True
                                        i = j + 1
                                        break
                                    else:
                                        # Continuation of description
                                        description_parts.append(next_line)
                                
                                if not found_amounts:
                                    i += 1
                        
                        except Exception as e:
                            print(f"⚠ Error parsing line {i}: {e}")
                            i += 1
                            continue
                    else:
                        i += 1
        
        print(f"✓ Extracted {len(output_data)} transactions from BNI PDF")
        
        if len(output_data) == 0:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(output_data)
        df = df.sort_values('DateTime').reset_index(drop=True)
        df = df.drop(columns=['DateTime'])
        
        # Attach metadata
        if account_info:
            df.attrs['account_info'] = account_info
        if summary_from_pdf:
            df.attrs['pdf_summary'] = summary_from_pdf
        
        return df
    
    except Exception as e:
        print(f"❌ Error processing BNI PDF: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def process_bni_excel(filepath):
    """Process BNI Excel format"""
    try:
        df = pd.read_excel(filepath)
        return process_bni_csv_dataframe(df)
    except Exception as e:
        print(f"Error processing BNI Excel: {e}")
        return pd.DataFrame()

def process_bni_csv_dataframe(df):
    """Process BNI dataframe (helper for CSV and Excel)"""
    output_data = []
    
    for idx, row in df.iterrows():
        if pd.isna(row.iloc[0]) or str(row.iloc[0]).lower() in ['tanggal', 'date', 'tgl']:
            continue
        
        try:
            # Find date
            date = None
            for col in df.columns:
                if any(keyword in str(col).lower() for keyword in ['tanggal', 'date', 'tgl']):
                    date = parse_bni_date(str(row[col]))
                    break
            
            if not date or pd.isna(date):
                continue
            
            # Find description
            description = ''
            for col in df.columns:
                if any(keyword in str(col).lower() for keyword in ['keterangan', 'description', 'uraian', 'remarks']):
                    description = str(row[col])
                    break
            
            # Find amounts
            debit = 0
            credit = 0
            balance = 0
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'debet' in col_lower or 'debit' in col_lower:
                    debit = clean_amount(row[col])
                elif 'kredit' in col_lower or 'credit' in col_lower:
                    credit = clean_amount(row[col])
                elif 'mutasi' in col_lower:
                    mutasi = clean_amount(row[col])
                    if mutasi > 0:
                        credit = mutasi
                    else:
                        debit = abs(mutasi)
                elif 'saldo' in col_lower or 'balance' in col_lower:
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

def process_bni_file(filepath, file_ext):
    """
    Main entry point for BNI processor
    Auto-detects format (CSV, PDF, Excel)
    """
    if file_ext == 'csv':
        return process_bni_csv(filepath)
    elif file_ext == 'pdf':
        return process_bni_pdf(filepath)
    elif file_ext in ['xlsx', 'xls']:
        return process_bni_excel(filepath)
    else:
        return pd.DataFrame()
