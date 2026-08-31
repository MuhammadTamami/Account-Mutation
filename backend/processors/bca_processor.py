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
    """Format number as Indonesian format"""
    if pd.isna(value) or value == 0:
        return "0,00"
    
    formatted = f"{value:.2f}"
    parts = formatted.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    integer_with_sep = f"{int(integer_part):,}"
    return f"{integer_with_sep},{decimal_part}"

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
    Process BCA PDF format using PyMuPDF (more robust than pdfplumber)
    Handles BCA Rekening Tahapan statement format with tabular layout
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(f"⚠ PyMuPDF not installed. Install with: pip install PyMuPDF")
        return pd.DataFrame()
    
    try:
        output_data = []
        account_info = {}
        
        doc = fitz.open(filepath)
        print(f"📄 Processing BCA PDF: {len(doc)} pages")
        
        # Extract account info from first page
        if len(doc) > 0:
            first_text = doc[0].get_text()
            lines = first_text.split('\n')
            
            for i, line in enumerate(lines):
                if 'NO. REKENING' in line or 'NO REKENING' in line:
                    # Account number is usually next line or after ':'
                    if i + 1 < len(lines):
                        acc_no = lines[i + 1].strip()
                        if acc_no == ':' and i + 2 < len(lines):
                            acc_no = lines[i + 2].strip()
                        account_info['accountNumber'] = acc_no
                
                # Find name (usually after address lines)
                if 'REKENING' in line and 'TAHAPAN' in line:
                    # Name is usually a few lines after
                    if i + 2 < len(lines):
                        name = lines[i + 2].strip()
                        if name and not any(skip in name for skip in ['KEC', 'KEL', 'DSN', 'KAB', ':']):
                            account_info['name'] = name
                
                if 'PERIODE' in line:
                    if i + 1 < len(lines):
                        period = lines[i + 1].strip()
                        if period == ':' and i + 2 < len(lines):
                            period = lines[i + 2].strip()
                        account_info['period'] = period
            
            if account_info:
                print(f"✓ Account: {account_info.get('name', '?')} ({account_info.get('accountNumber', '?')})")
        
        # Get year from period for date parsing
        year = None
        if 'period' in account_info:
            period_match = re.search(r'(\d{4})', account_info['period'])
            if period_match:
                year = period_match.group(1)
        
        if not year:
            print(f"⚠ Could not extract year from period")
            return pd.DataFrame()
        
        # Process all pages for transactions
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            lines = text.split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines and headers
                if not line:
                    i += 1
                    continue
                
                # Skip known header/footer keywords
                if any(kw in line for kw in ['REKENING', 'HALAMAN', 'PERIODE', 'MATA UANG', 'CATATAN', 'Bersambung', 'TANGGAL', 'KETERANGAN', 'CBG', 'MUTASI', 'SALDO']):
                    i += 1
                    continue
                
                # Look for date pattern at start of line: DD/MM
                date_match = re.match(r'^(\d{2}/\d{2})$', line)
                
                if date_match:
                    try:
                        date_str = date_match.group(1)  # DD/MM
                        date = pd.to_datetime(f"{date_str}/{year}", format='%d/%m/%Y')
                        
                        # Collect description, reference, branch, amounts from next lines
                        description_parts = []
                        reference = '-'
                        branch = ''
                        amount = 0.0
                        balance = 0.0
                        transaction_type = None
                        
                        # Look at next 20 lines for transaction details
                        for j in range(i + 1, min(i + 20, len(lines))):
                            next_line = lines[j].strip()
                            
                            if not next_line:
                                continue
                            
                            # Stop if we hit another date
                            if re.match(r'^\d{2}/\d{2}$', next_line):
                                i = j - 1  # Back up to process this date
                                break
                            
                            # Check if this line is a branch code (4 digits)
                            if re.match(r'^\d{4}$', next_line):
                                branch = next_line
                                continue
                            
                            # Check if line contains amount (Indonesian format: 123,456.78 or 123,456,789.12)
                            # Amounts can be on same line as branch or separate
                            amount_match = re.search(r'([\d,]+\.\d{2})', next_line)
                            
                            if amount_match:
                                amount_str = amount_match.group(1)
                                amount = clean_amount(amount_str)
                                
                                # Check if there's another amount after this (balance)
                                # Look for next amount in this line or next few lines
                                remainder = next_line[amount_match.end():].strip()
                                balance_match = re.search(r'([\d,]+\.\d{2})', remainder)
                                
                                if balance_match:
                                    balance = clean_amount(balance_match.group(1))
                                else:
                                    # Balance might be on next line
                                    if j + 1 < len(lines):
                                        next_next = lines[j + 1].strip()
                                        balance_match = re.match(r'^([\d,]+\.\d{2})$', next_next)
                                        if balance_match:
                                            balance = clean_amount(balance_match.group(1))
                                
                                # Determine type: if description contains "DB" or starts with debit keywords
                                desc_text = ' '.join(description_parts).upper()
                                if 'TRSF' in desc_text or 'TARIKAN' in desc_text or 'PAJAK' in desc_text or 'BIAYA' in desc_text:
                                    transaction_type = 'Debit'
                                else:
                                    transaction_type = 'Credit'
                                
                                break
                            else:
                                # This is description or reference line
                                # Check for MID/reference patterns
                                if 'MID :' in next_line or re.match(r'^\d{4}/', next_line):
                                    reference = next_line
                                
                                description_parts.append(next_line)
                        
                        # If we found an amount, add transaction
                        if amount > 0 and transaction_type:
                            description = ' '.join(description_parts).strip()
                            description = ' '.join(description.split())  # Clean multiple spaces
                            
                            output_data.append({
                                'Date': date,
                                'Reference': reference,
                                'Description': description,
                                'Type': transaction_type,
                                'Amount': format_indonesian_number(amount),
                                'Balance': format_indonesian_number(balance)
                            })
                    
                    except Exception as e:
                        print(f"⚠ Error parsing line {i} on page {page_num + 1}: {e}")
                
                i += 1
        
        doc.close()
        
        print(f"✓ Extracted {len(output_data)} transactions from BCA PDF")
        
        if len(output_data) == 0:
            print(f"⚠ No transactions extracted")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(output_data)
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Attach metadata
        if account_info:
            df.attrs['account_info'] = account_info
        
        return df
    
    except Exception as e:
        print(f"❌ Error processing BCA PDF: {e}")
        print(f"⚠ BCA PDF format may be complex or image-based")
        print(f"✅ SOLUTION: Export to CSV/Excel from BCA Internet Banking and upload")
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
