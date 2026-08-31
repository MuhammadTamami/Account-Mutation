"""
BRI Bank Statement Processor
Supports CSV, PDF, and Excel formats
"""
import pandas as pd
import pdfplumber
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert BRI number format to float - BRI uses English format (comma=thousands, dot=decimal)"""
    if pd.isna(amount_str) or amount_str == '' or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip()
    amount_str = amount_str.replace('Rp', '').replace('IDR', '').strip()
    
    # BRI e-Statement uses ENGLISH format: 1,234,567.89
    # Comma is thousand separator, dot is decimal separator
    # Remove commas, keep dots
    amount_str = amount_str.replace(',', '')
    
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

def parse_bri_date(date_str):
    """Parse BRI date formats"""
    try:
        for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y', '%Y-%m-%d', '%d.%m.%Y']:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except:
                continue
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

def process_bri_csv(filepath):
    """Process BRI CSV format"""
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
                        date = parse_bri_date(str(row[col]))
                        break
                
                if not date or pd.isna(date):
                    continue
                
                # Find description
                description = ''
                for col in df.columns:
                    if any(keyword in str(col).lower() for keyword in ['keterangan', 'description', 'deskripsi', 'uraian']):
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
        print(f"Error processing BRI CSV: {e}")
        return pd.DataFrame()

def process_bri_pdf(filepath):
    """
    Process BRI PDF format - supports BRI e-Statement from BRImo
    Format: Date Time | Description | Teller | Debit | Credit | Balance
    """
    try:
        output_data = []
        account_info = None
        summary_data = None
        
        with pdfplumber.open(filepath) as pdf:
            print(f"📄 Processing BRI PDF: {len(pdf.pages)} pages")
            
            # Extract account info from page 1
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                first_text = first_page.extract_text()
                
                if first_text:
                    account_data = {}
                    
                    # Extract Account Number (No. Rekening)
                    acc_no_match = re.search(r'No\.\s+Rekening\s*:\s*(\d+)', first_text, re.IGNORECASE)
                    if acc_no_match:
                        account_data['accountNumber'] = acc_no_match.group(1).strip()
                    
                    # Extract Account Name
                    # Example: "HARFANI Periode Transaksi : 01/01/26 - 31/01/26"
                    # The name appears right before "Periode Transaksi" on the same line or after newline
                    name_match = re.search(r'([A-Z][A-Z ]{2,50}?)\s+Periode\s+Transaksi', first_text, re.IGNORECASE)
                    if name_match:
                        # Get the last line only (in case there's a newline)
                        name_raw = name_match.group(1).strip()
                        # Take only the last line if there are multiple lines
                        name_lines = name_raw.split('\n')
                        account_data['name'] = name_lines[-1].strip()
                    
                    # Extract Product Name (Nama Produk)
                    product_match = re.search(r'Nama Produk\s*:\s*([A-Za-z\s]+?)(?:\n|Alamat)', first_text, re.IGNORECASE)
                    if product_match:
                        account_data['product'] = product_match.group(1).strip()
                    
                    # Extract Branch (Unit Kerja)
                    branch_match = re.search(r'Unit Kerja\s*:\s*([A-Za-z\s]+?)(?:\n|Alamat)', first_text, re.IGNORECASE)
                    if branch_match:
                        account_data['branch'] = branch_match.group(1).strip()
                    
                    # Extract Period
                    period_match = re.search(r'Periode Transaksi\s*:\s*(\d{2}/\d{2}/\d{2})\s*-\s*(\d{2}/\d{2}/\d{2})', first_text, re.IGNORECASE)
                    if period_match:
                        account_data['periodStart'] = period_match.group(1)
                        account_data['periodEnd'] = period_match.group(2)
                    
                    if account_data:
                        account_info = account_data
                        print(f"✓ Account: {account_data.get('name', '?')} ({account_data.get('accountNumber', '?')})")
            
            # Process all pages for transactions
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                
                if not text:
                    continue
                
                lines = text.split('\n')
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Skip headers, footers, and empty lines
                    if not line:
                        i += 1
                        continue
                    
                    if any(keyword in line.upper() for keyword in [
                        'LAPORAN TRANSAKSI', 'STATEMENT OF', 'HALAMAN', 'PAGE', 
                        'TANGGAL TRANSAKSI', 'TRANSACTION DATE', 'TRANSACTION DESCRIPTION',
                        'URAIAN TRANSAKSI', 'DEBET', 'KREDIT', 'SALDO', 'DEBIT', 'CREDIT', 'BALANCE'
                    ]):
                        i += 1
                        continue
                    
                    # BRI e-Statement Format:
                    # DD/MM/YY HH:MM:SS Description Teller Debit Credit Balance
                    # Example: "01/01/26 04:24:21 OffUs 1 251231 001999170845 TOKO MAKITA BRIMTXDT 0.00 590,040.00 171,418,357.81"
                    
                    # Match date and time at the beginning
                    datetime_match = re.match(r'^(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})', line)
                    
                    if datetime_match:
                        try:
                            date_str = datetime_match.group(1)
                            time_str = datetime_match.group(2)
                            
                            # Parse date (format: DD/MM/YY)
                            # Convert YY to full year (26 -> 2026)
                            day, month, year = date_str.split('/')
                            full_year = f"20{year}" if int(year) < 50 else f"19{year}"
                            full_date_str = f"{day}/{month}/{full_year}"
                            
                            date = pd.to_datetime(full_date_str, format='%d/%m/%Y')
                            datetime_obj = pd.to_datetime(f"{full_date_str} {time_str}", format='%d/%m/%Y %H:%M:%S')
                            
                            # Extract the rest of the line after datetime
                            rest_of_line = line[datetime_match.end():].strip()
                            
                            # Look for amounts (last 3 numbers in the line)
                            # BRI uses dot for thousands, comma for decimals: 590,040.00 or 171,418,357.81
                            # Also handle cases with only 2 numbers (debit/credit and balance)
                            numbers = re.findall(r'[\d,]+\.[\d]{2}', rest_of_line)
                            
                            if len(numbers) >= 3:
                                # Standard format: Debit, Credit, Balance
                                debit_str = numbers[-3]
                                credit_str = numbers[-2]
                                balance_str = numbers[-1]
                                
                                # Remove amounts from line to get description + teller
                                desc_line = rest_of_line
                                for num in numbers[-3:]:
                                    desc_line = desc_line.replace(num, '', 1)
                                
                                # Extract teller ID (usually alphanumeric code like BRIMTXDT, 8888673, 0371854)
                                # Teller ID is usually right before the amounts
                                desc_parts = desc_line.strip().rsplit(None, 1)
                                if len(desc_parts) == 2:
                                    description = desc_parts[0].strip()
                                    teller = desc_parts[1].strip()
                                else:
                                    description = desc_line.strip()
                                    teller = '-'
                                
                                # Clean up description
                                description = ' '.join(description.split())
                                
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
                                    # Skip if both are zero or both have values
                                    i += 1
                                    continue
                                
                                output_data.append({
                                    'DateTime': datetime_obj,
                                    'OriginalIndex': len(output_data),
                                    'Date': date,
                                    'Reference': teller,
                                    'Description': description,
                                    'Type': transaction_type,
                                    'Amount': format_indonesian_number(amount),
                                    'Balance': format_indonesian_number(balance)
                                })
                                
                            elif len(numbers) == 2:
                                # Sometimes balance might be on next line, or it's a special format
                                # Try to get balance from next line
                                balance_str = numbers[-1]
                                amount_str = numbers[-2]
                                
                                # Determine if it's debit or credit based on description keywords
                                desc_lower = rest_of_line.lower()
                                
                                # Default: treat as credit
                                credit = clean_amount(amount_str)
                                debit = 0
                                
                                # Check if it's a debit transaction
                                if any(keyword in desc_lower for keyword in ['pembayaran', 'biaya', 'tarif', 'transfer ke', 'bayar']):
                                    debit = clean_amount(amount_str)
                                    credit = 0
                                
                                balance = clean_amount(balance_str)
                                
                                # Extract description and teller
                                desc_line = rest_of_line
                                for num in numbers:
                                    desc_line = desc_line.replace(num, '', 1)
                                
                                desc_parts = desc_line.strip().rsplit(None, 1)
                                if len(desc_parts) == 2:
                                    description = desc_parts[0].strip()
                                    teller = desc_parts[1].strip()
                                else:
                                    description = desc_line.strip()
                                    teller = '-'
                                
                                description = ' '.join(description.split())
                                
                                # Determine transaction type
                                if credit > 0:
                                    transaction_type = 'Credit'
                                    amount = credit
                                elif debit > 0:
                                    transaction_type = 'Debit'
                                    amount = debit
                                else:
                                    i += 1
                                    continue
                                
                                output_data.append({
                                    'DateTime': datetime_obj,
                                    'OriginalIndex': len(output_data),
                                    'Date': date,
                                    'Reference': teller,
                                    'Description': description,
                                    'Type': transaction_type,
                                    'Amount': format_indonesian_number(amount),
                                    'Balance': format_indonesian_number(balance)
                                })
                            
                            i += 1
                        
                        except Exception as e:
                            print(f"⚠ Error parsing line {i}: {e}")
                            i += 1
                            continue
                    else:
                        i += 1
        
        if not output_data:
            print(f"⚠ No transactions found in PDF")
            return pd.DataFrame()
        
        print(f"✓ Extracted {len(output_data)} transactions")
        
        # Create DataFrame
        result_df = pd.DataFrame(output_data)
        
        # Sort by DateTime first, then by OriginalIndex
        result_df = result_df.sort_values(['DateTime', 'OriginalIndex']).reset_index(drop=True)
        
        # Drop helper columns
        result_df = result_df.drop(columns=['DateTime', 'OriginalIndex'])
        
        # Attach account info as metadata
        if account_info:
            result_df.attrs['account_info'] = account_info
        
        return result_df
    
    except Exception as e:
        print(f"❌ Error processing BRI PDF: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def process_bri_excel(filepath):
    """Process BRI Excel format"""
    try:
        df = pd.read_excel(filepath)
        return process_bri_csv_dataframe(df)
    except Exception as e:
        print(f"Error processing BRI Excel: {e}")
        return pd.DataFrame()

def process_bri_csv_dataframe(df):
    """Process BRI dataframe (helper for CSV and Excel)"""
    output_data = []
    
    for idx, row in df.iterrows():
        if pd.isna(row.iloc[0]) or str(row.iloc[0]).lower() in ['tanggal', 'date', 'tgl']:
            continue
        
        try:
            # Find date
            date = None
            for col in df.columns:
                if any(keyword in str(col).lower() for keyword in ['tanggal', 'date', 'tgl']):
                    date = parse_bri_date(str(row[col]))
                    break
            
            if not date or pd.isna(date):
                continue
            
            # Find description
            description = ''
            for col in df.columns:
                if any(keyword in str(col).lower() for keyword in ['keterangan', 'description', 'uraian']):
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

def process_bri_file(filepath, file_ext):
    """
    Main entry point for BRI processor
    Auto-detects format (CSV, PDF, Excel)
    """
    if file_ext == 'csv':
        return process_bri_csv(filepath)
    elif file_ext == 'pdf':
        return process_bri_pdf(filepath)
    elif file_ext in ['xlsx', 'xls']:
        return process_bri_excel(filepath)
    else:
        return pd.DataFrame()
