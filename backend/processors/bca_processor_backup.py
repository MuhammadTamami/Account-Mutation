"""
BCA Bank Statement Processor
Supports CSV, PDF, and Excel formats
"""
import pandas as pd
import pdfplumber
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert BCA number format to float"""
    if pd.isna(amount_str) or amount_str == '' or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip()
    
    # Remove currency symbols
    amount_str = amount_str.replace('Rp', '').replace('IDR', '').strip()
    
    # BCA typically uses: 1.234.567,89 (dot=thousand, comma=decimal)
    if ',' in amount_str and '.' in amount_str:
        # Indonesian format: remove dots, replace comma with dot
        amount_str = amount_str.replace('.', '').replace(',', '.')
    elif ',' in amount_str:
        # Only comma - assume decimal
        amount_str = amount_str.replace(',', '.')
    elif '.' in amount_str:
        # Only dot - check if thousand or decimal
        parts = amount_str.split('.')
        if len(parts[-1]) == 3 and len(parts) > 1:
            # Thousand separator
            amount_str = amount_str.replace('.', '')
    
    try:
        return float(amount_str)
    except:
        return 0.0

def format_indonesian_number(value):
    """Format number as International format: 18,000,000.00"""
    if pd.isna(value) or value == 0:
        return "0.00"
    
    # Use standard US locale format (comma for thousands, dot for decimal)
    formatted = f"{value:,.2f}"
    return formatted

def parse_bca_date(date_str):
    """Parse BCA date formats"""
    try:
        # Common BCA formats: DD/MM/YYYY, DD-MM-YYYY, DD MMM YYYY
        for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y', '%Y-%m-%d']:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except:
                continue
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

def process_bca_csv(filepath):
    """Process BCA CSV format"""
    try:
        # Try different separators and encodings
        for sep in [',', ';', '\t']:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, sep=sep, encoding=encoding)
                    if len(df.columns) > 3:
                        break
                except:
                    continue
        
        # BCA CSV typically has columns: Tanggal, Keterangan, Mutasi, Saldo
        # Or: Date, Description, Debit, Credit, Balance
        
        output_data = []
        
        for idx, row in df.iterrows():
            # Skip header rows
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).lower() in ['tanggal', 'date', 'tgl']:
                continue
            
            try:
                # Try to find date column
                date = None
                for col in df.columns:
                    if 'tanggal' in col.lower() or 'date' in col.lower() or 'tgl' in col.lower():
                        date = parse_bca_date(str(row[col]))
                        break
                
                if not date or pd.isna(date):
                    continue
                
                # Find description
                description = ''
                for col in df.columns:
                    if 'keterangan' in col.lower() or 'description' in col.lower() or 'deskripsi' in col.lower():
                        description = str(row[col])
                        break
                
                # Find amounts (debit/credit or mutasi)
                debit = 0
                credit = 0
                balance = 0
                
                for col in df.columns:
                    col_lower = col.lower()
                    if 'debit' in col_lower or 'db' == col_lower:
                        debit = clean_amount(row[col])
                    elif 'credit' in col_lower or 'cr' == col_lower or 'kredit' in col_lower:
                        credit = clean_amount(row[col])
                    elif 'mutasi' in col_lower:
                        mutasi = clean_amount(row[col])
                        if mutasi > 0:
                            credit = mutasi
                        else:
                            debit = abs(mutasi)
                    elif 'saldo' in col_lower or 'balance' in col_lower:
                        balance = clean_amount(row[col])
                
                # Determine transaction type
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
        print(f"Error processing BCA CSV: {e}")
        return pd.DataFrame()

def process_bca_pdf(filepath):
    """
    Process BCA PDF format using PyMuPDF
    
    Rules for extraction:
    1. Type detection: Check if amount line has "DB" suffix
       - Has "DB" → Debit
       - No "DB" → Credit
    2. Balance: Extract from lines that show balance (after net amount)
    3. Amount: Use net amount (after DDR line)
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(f"WARNING: PyMuPDF not installed. Install with: pip install PyMuPDF")
        return pd.DataFrame()
    
    try:
        output_data = []
        account_info = {}
        
        doc = fitz.open(filepath)
        print(f"Processing BCA PDF: {len(doc)} pages")
        
        # Extract account info and summary from first and last page
        if len(doc) > 0:
            first_text = doc[0].get_text()
            lines = first_text.split('\n')
            
            for i, line in enumerate(lines):
                if 'NO. REKENING' in line or 'NO REKENING' in line:
                    if i + 1 < len(lines):
                        acc_no = lines[i + 1].strip()
                        if acc_no == ':' and i + 2 < len(lines):
                            acc_no = lines[i + 2].strip()
                        account_info['accountNumber'] = acc_no
                
                if 'PERIODE' in line:
                    if i + 1 < len(lines):
                        period = lines[i + 1].strip()
                        if period == ':' and i + 2 < len(lines):
                            period = lines[i + 2].strip()
                        account_info['period'] = period
            
            # Try to find name (look for capitalized name before address keywords)
            for i, line in enumerate(lines):
                if line.strip() and len(line.strip()) > 5:
                    # Check if next lines contain address keywords
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if any(kw in next_line for kw in ['KEC', 'KEL', 'DSN', 'KAB']):
                            # This line is likely the name
                            name = line.strip()
                            if not any(skip in name for skip in ['REKENING', 'TAHAPAN', 'KCP', 'NO.']):
                                account_info['name'] = name
                                break
            
            if account_info:
                print(f"OK Account: {account_info.get('name', '?')} ({account_info.get('accountNumber', '?')})")
        
        # Extract summary from last page
        summary = {}
        if len(doc) > 0:
            last_text = doc[-1].get_text()
            last_lines = last_text.split('\n')
            
            for i, line in enumerate(last_lines):
                line_stripped = line.strip()
                
                if 'SALDO AWAL' in line_stripped:
                    # Look for amount in next few lines (skip :)
                    for j in range(i + 1, min(i + 5, len(last_lines))):
                        val = last_lines[j].strip().replace(':', '').strip()
                        if val and ',' in val and '.' in val:
                            summary['saldo_awal'] = clean_amount(val)
                            break
                
                elif line_stripped == 'MUTASI CR':  # Exact match
                    # Look for amount in next few lines (skip :)
                    for j in range(i + 1, min(i + 5, len(last_lines))):
                        val = last_lines[j].strip().replace(':', '').strip()
                        if val and ',' in val and '.' in val:
                            summary['mutasi_cr'] = clean_amount(val)
                            # Count is next numeric line
                            for k in range(j + 1, min(j + 3, len(last_lines))):
                                if last_lines[k].strip().isdigit():
                                    summary['count_cr'] = int(last_lines[k].strip())
                                    break
                            break
                
                elif line_stripped == 'MUTASI DB':  # Exact match
                    # Look for amount in next few lines (skip :)
                    for j in range(i + 1, min(i + 5, len(last_lines))):
                        val = last_lines[j].strip().replace(':', '').strip()
                        if val and ',' in val and '.' in val:
                            summary['mutasi_db'] = clean_amount(val)
                            # Count is next numeric line
                            for k in range(j + 1, min(j + 3, len(last_lines))):
                                if last_lines[k].strip().isdigit():
                                    summary['count_db'] = int(last_lines[k].strip())
                                    break
                            break
                
                elif 'SALDO AKHIR' in line_stripped:
                    # Look for amount in next few lines (skip :)
                    for j in range(i + 1, min(i + 5, len(last_lines))):
                        val = last_lines[j].strip().replace(':', '').strip()
                        if val and ',' in val and '.' in val:
                            summary['saldo_akhir'] = clean_amount(val)
                            break
        
        if summary:
            print(f"OK Summary: CR {summary.get('count_cr', '?')} txns, DB {summary.get('count_db', '?')} txns")
        
        # Get year from period for date parsing
        year = None
        if 'period' in account_info:
            period_match = re.search(r'(\d{4})', account_info['period'])
            if period_match:
                year = period_match.group(1)
        
        if not year:
            print(f"WARNING: Could not extract year from period")
            return pd.DataFrame()
        
        # Process all pages for transactions
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            lines = text.split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines
                if not line:
                    i += 1
                    continue
                
                # Skip headers
                if any(kw in line for kw in ['REKENING', 'HALAMAN', 'PERIODE', 'MATA UANG', 'CATATAN', 'Bersambung', 'TANGGAL', 'KETERANGAN', 'CBG', 'MUTASI', 'SALDO']):
                    i += 1
                    continue
                
                # Look for date pattern: DD/MM
                date_match = re.match(r'^(\d{2}/\d{2})$', line)
                
                if date_match:
                    try:
                        date_str = date_match.group(1)
                        date = pd.to_datetime(f"{date_str}/{year}", format='%d/%m/%Y')
                        
                        # Collect description and amounts
                        description_parts = []
                        amount = 0.0
                        balance = 0.0
                        transaction_type = None
                        branch = ''
                        
                        # Look at next lines for transaction details
                        j = i + 1
                        found_amount = False
                        
                        while j < min(i + 25, len(lines)):
                            next_line = lines[j].strip()
                            
                            # Stop if we hit another date
                            if re.match(r'^\d{2}/\d{2}$', next_line):
                                break
                            
                            # Skip empty lines
                            if not next_line:
                                j += 1
                                continue
                            
                            # Check for branch code (4 digits)
                            if re.match(r'^\d{4}$', next_line):
                                branch = next_line
                                j += 1
                                continue
                            
                            # Skip QR/TGH/DDR lines (these are intermediate values)
                            if next_line.startswith('QR :') or next_line.startswith('TGH:') or next_line.startswith('DDR:'):
                                j += 1
                                continue
                            
                            # Check for net amount line
                            # Format: "123,456.78" or "123,456.78 DB"
                            # Can appear with or without branch code
                            amount_pattern = r'^([\d,]+\.\d{2})(\s+DB)?$'
                            amount_match = re.match(amount_pattern, next_line)
                            
                            if amount_match:
                                # Check if we have enough context (either branch or description)
                                has_context = branch or len(description_parts) > 0
                                
                                if has_context:
                                    amount = clean_amount(amount_match.group(1))
                                    has_db = amount_match.group(2) is not None
                                    
                                    # Type detection: Has " DB" suffix = Debit, No " DB" = Credit
                                    transaction_type = 'Debit' if has_db else 'Credit'
                                    found_amount = True
                                    
                                    # Look for balance in next few lines
                                    for k in range(j + 1, min(j + 5, len(lines))):
                                        bal_line = lines[k].strip()
                                        # Balance is a standalone amount (no DB suffix, with comma)
                                        if re.match(r'^[\d,]+\.\d{2}$', bal_line):
                                            # Make sure it's not another transaction amount
                                            # Balance usually larger than individual transaction
                                            bal_amt = clean_amount(bal_line)
                                            if bal_amt > amount:  # Simple heuristic
                                                balance = bal_amt
                                                break
                                    
                                    break
                            else:
                                # This is description
                                if not next_line.startswith(('MID', ':', 'QR', 'TGH', 'DDR')) and not next_line.isdigit():
                                    description_parts.append(next_line)
                            
                            j += 1
                        
                        # Add transaction if we found amount
                        if found_amount and transaction_type:
                            description = ' '.join(description_parts).strip()
                            description = ' '.join(description.split())  # Clean spaces
                            
                            output_data.append({
                                'Date': date,
                                'Reference': branch if branch else '-',
                                'Description': description,
                                'Type': transaction_type,
                                'Amount': format_indonesian_number(amount),
                                'Balance': format_indonesian_number(balance) if balance > 0 else '0.00'
                            })
                        
                        # Move to where we stopped
                        i = j
                    
                    except Exception as e:
                        print(f"WARNING: Error parsing line {i} on page {page_num + 1}: {e}")
                        i += 1
                else:
                    i += 1
        
        doc.close()
        
        print(f"OK Extracted {len(output_data)} transactions from BCA PDF")
        
        if len(output_data) == 0:
            print(f"WARNING: No transactions extracted")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(output_data)
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Attach metadata
        if account_info:
            df.attrs['account_info'] = account_info
        if summary:
            df.attrs['summary'] = summary
        
        # Validate against summary
        if summary:
            actual_cr = len(df[df['Type'] == 'Credit'])
            actual_db = len(df[df['Type'] == 'Debit'])
            expected_cr = summary.get('count_cr', 0)
            expected_db = summary.get('count_db', 0)
            
            if actual_cr != expected_cr or actual_db != expected_db:
                print(f"WARNING: Count mismatch: CR {actual_cr}/{expected_cr}, DB {actual_db}/{expected_db}")
            else:
                print(f"OK Validation passed: CR {actual_cr}, DB {actual_db}")
        
        return df
    
    except Exception as e:
        print(f"ERROR: Error processing BCA PDF: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def process_bca_excel(filepath):
    """Process BCA Excel format"""
    try:
        # Read Excel file
        df = pd.read_excel(filepath)
        
        # Process similar to CSV
        return process_bca_csv_dataframe(df)
    
    except Exception as e:
        print(f"Error processing BCA Excel: {e}")
        return pd.DataFrame()

def process_bca_csv_dataframe(df):
    """Process BCA dataframe (helper for CSV and Excel)"""
    output_data = []
    
    for idx, row in df.iterrows():
        # Skip header rows
        if pd.isna(row.iloc[0]) or str(row.iloc[0]).lower() in ['tanggal', 'date', 'tgl']:
            continue
        
        try:
            # Find date
            date = None
            for col in df.columns:
                if 'tanggal' in str(col).lower() or 'date' in str(col).lower() or 'tgl' in str(col).lower():
                    date = parse_bca_date(str(row[col]))
                    break
            
            if not date or pd.isna(date):
                continue
            
            # Find description
            description = ''
            for col in df.columns:
                if 'keterangan' in str(col).lower() or 'description' in str(col).lower():
                    description = str(row[col])
                    break
            
            # Find amounts
            debit = 0
            credit = 0
            balance = 0
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'debit' in col_lower or 'db' == col_lower:
                    debit = clean_amount(row[col])
                elif 'credit' in col_lower or 'cr' == col_lower or 'kredit' in col_lower:
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

def process_bca_file(filepath, file_ext):
    """
    Main entry point for BCA processor
    Auto-detects format (CSV, PDF, Excel)
    """
    if file_ext == 'csv':
        return process_bca_csv(filepath)
    elif file_ext == 'pdf':
        return process_bca_pdf(filepath)
    elif file_ext in ['xlsx', 'xls']:
        return process_bca_excel(filepath)
    else:
        return pd.DataFrame()
