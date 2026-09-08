"""
BSI Bank Statement Processor
Supports CSV, PDF, and Excel formats
"""
import pandas as pd
import pdfplumber
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert Indonesian number format to float
    Handles negative values (e.g., "-2,500.00")
    """
    if pd.isna(amount_str) or amount_str == '':
        return 0.0
    
    # Remove currency symbols and spaces
    amount_str = str(amount_str).strip()
    
    # Check if it's "0.00" or "0,00"
    if amount_str in ['0.00', '0,00', '0']:
        return 0.0
    
    # Handle negative sign
    is_negative = amount_str.startswith('-')
    if is_negative:
        amount_str = amount_str[1:]  # Remove negative sign
    
    # Remove thousand separator (comma or dot depending on format)
    # BSI format: 630,000.00 (comma = thousand, dot = decimal)
    # OR: 630.000,00 (dot = thousand, comma = decimal)
    
    if ',' in amount_str and '.' in amount_str:
        # Both present - check which comes last
        last_comma = amount_str.rfind(',')
        last_dot = amount_str.rfind('.')
        
        if last_dot > last_comma:
            # English format: 1,234.56
            amount_str = amount_str.replace(',', '')
        else:
            # Indonesian format: 1.234,56
            amount_str = amount_str.replace('.', '').replace(',', '.')
    elif ',' in amount_str:
        # Only comma - assume thousand separator
        amount_str = amount_str.replace(',', '')
    elif '.' in amount_str:
        # Only dot - could be decimal or thousand
        # If there are 3 digits after the last dot, it's thousand separator
        # Otherwise it's decimal
        parts = amount_str.split('.')
        if len(parts[-1]) == 3 and len(parts) > 1:
            # Thousand separator
            amount_str = amount_str.replace('.', '')
        # else: keep as decimal
    
    try:
        value = float(amount_str)
        return -value if is_negative else value
    except:
        return 0.0

def format_indonesian_number(value):
    """Format number as International format: 18,000,000.00"""
    if pd.isna(value) or value == 0:
        return "0.00"
    
    # Use standard US locale format (comma for thousands, dot for decimal)
    formatted = f"{value:,.2f}"
    return formatted

def parse_date_time(date_str):
    """Parse BSI date format: 2026-03-01 / 05:12:01
    Returns tuple of (date, datetime)
    """
    try:
        # Split by ' / '
        parts = date_str.split(' / ')
        date_part = parts[0]
        time_part = parts[1] if len(parts) > 1 else '00:00:00'
        
        # Combine date and time
        datetime_str = f"{date_part} {time_part}"
        datetime_obj = pd.to_datetime(datetime_str)
        date_obj = pd.to_datetime(date_part)
        
        return date_obj, datetime_obj
    except:
        return pd.NaT, pd.NaT

def process_bsi_csv(filepath):
    """
    Process BSI bank statement CSV file
    
    Expected columns:
    No;Tgl dan Waktu Periode;No Referensi;Deskripsi;Kode;D/K;Debit;Kredit;Saldo
    OR
    "No.","Tgl dan Waktu Periode","No Referensi","Deskripsi","Kode","D/K","Debit","Kredit","Saldo",""
    """
    
    # Try to detect separator (semicolon or comma)
    # Read first line to check
    with open(filepath, 'r', encoding='utf-8') as f:
        first_line = f.readline()
    
    # Detect separator
    if first_line.count(';') > first_line.count(','):
        separator = ';'
    else:
        separator = ','
    
    # Read CSV with detected delimiter
    df = pd.read_csv(filepath, sep=separator, encoding='utf-8')
    
    return process_bsi_dataframe(df)

def process_bsi_dataframe(df):
    """Process BSI dataframe (helper for CSV and Excel)"""
    # Filter out summary rows and header rows
    df = df[df['No.'].notna()]
    df = df[df['No.'] != 'No.']
    
    # Create standardized output
    output_data = []
    
    for idx, row in df.iterrows():
        # Skip if no date
        if pd.isna(row['Tgl dan Waktu Periode']):
            continue
            
        date, datetime_obj = parse_date_time(row['Tgl dan Waktu Periode'])
        
        # Determine transaction type and amount
        debit = clean_amount(row['Debit'])
        credit = clean_amount(row['Kredit'])
        
        if credit > 0:
            transaction_type = 'Credit'
            amount = credit
        elif debit != 0:  # Debit could be negative
            transaction_type = 'Debit'
            amount = abs(debit)  # Make positive for display
        else:
            continue  # Skip if no amount
        
        output_data.append({
            'DateTime': datetime_obj,
            'OriginalIndex': idx,  # Track original CSV order
            'Date': date,
            'Reference': row['No Referensi'],
            'Description': row['Deskripsi'],
            'Type': transaction_type,
            'Amount': format_indonesian_number(amount),
            'Balance': format_indonesian_number(clean_amount(row['Saldo']))
        })
    
    # Create DataFrame
    result_df = pd.DataFrame(output_data)
    
    # Sort by DateTime first, then by OriginalIndex (to preserve order when times are identical)
    result_df = result_df.sort_values(['DateTime', 'OriginalIndex']).reset_index(drop=True)
    
    # Drop helper columns
    result_df = result_df.drop(columns=['DateTime', 'OriginalIndex'])
    
    return result_df

def process_bsi_pdf(filepath):
    """Process BSI PDF format"""
    try:
        output_data = []
        
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for line in lines:
                    # Skip headers and empty lines
                    if not line.strip() or 'TANGGAL' in line.upper() or 'NO REFERENSI' in line.upper():
                        continue
                    
                    # Look for date pattern: DD/MM/YYYY / HH:MM:SS
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})\s*/\s*(\d{2}:\d{2}:\d{2})', line)
                    
                    if date_match:
                        try:
                            date_str = date_match.group(1)
                            time_str = date_match.group(2)
                            
                            date = pd.to_datetime(date_str)
                            datetime_obj = pd.to_datetime(f"{date_str} {time_str}")
                            
                            # Extract transaction details from line
                            # BSI PDF format typically: Date/Time | RefNo | Description | Type | Amount | Balance
                            parts = line.split()
                            
                            # Find numbers (amounts)
                            numbers = re.findall(r'[\d,]+\.[\d]{2}', line)
                            
                            if len(numbers) >= 2:
                                # Description is between date and amounts
                                desc_start = line.find(time_str) + len(time_str)
                                desc_end = line.find(numbers[-2]) if len(numbers) > 1 else line.find(numbers[-1])
                                description = line[desc_start:desc_end].strip()
                                
                                # Parse amounts - last 2 are usually amount and balance
                                if len(numbers) >= 2:
                                    amount_str = numbers[-2]
                                    balance_str = numbers[-1]
                                    
                                    amount = clean_amount(amount_str)
                                    balance = clean_amount(balance_str)
                                    
                                    
                                    # PRIMARY: Balance-based detection (compare with previous transaction)
                                    if output_data and len(output_data) > 0:
                                        # Get previous balance
                                        prev_balance_str = output_data[-1]['Balance']
                                        prev_balance = float(prev_balance_str.replace(',', ''))
                                        
                                        # Compare: if balance increased = Credit, if decreased = Debit
                                        balance_diff = balance - prev_balance
                                        
                                        if balance_diff > 0:
                                            transaction_type = 'Credit'
                                        elif balance_diff < 0:
                                            transaction_type = 'Debit'
                                        else:
                                            # Balance unchanged, skip
                                            continue
                                    else:
                                        # FALLBACK: For first transaction, use enhanced keyword detection
                                        line_upper = line.upper()
                                        
                                        # Credit indicators
                                        if any(kw in line_upper for kw in ['CREDIT', 'CR', 'KREDIT', 'INCOMING', 'TRANSFER IN', 'DEPOSIT']):
                                            transaction_type = 'Credit'
                                        # Debit indicators
                                        elif any(kw in line_upper for kw in ['DEBIT', 'DB', 'WITHDRAWAL', 'TRANSFER OUT', 'FEE', 'BIAYA', 'ADMIN']):
                                            transaction_type = 'Debit'
                                        else:
                                            # Last resort: amount sign
                                            transaction_type = 'Credit' if amount > 0 else 'Debit'
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
        print(f"Error processing BSI PDF: {e}")
        return pd.DataFrame()

def process_bsi_excel(filepath):
    """Process BSI Excel format"""
    try:
        # Read Excel file
        df = pd.read_excel(filepath)
        
        # Check if it has BSI column structure
        if 'Tgl dan Waktu Periode' in df.columns and 'Deskripsi' in df.columns:
            return process_bsi_dataframe(df)
        else:
            # Try to find columns by keywords
            # Rename columns if needed
            column_mapping = {}
            for col in df.columns:
                col_lower = str(col).lower()
                if 'tanggal' in col_lower or 'tgl' in col_lower or 'waktu' in col_lower:
                    column_mapping[col] = 'Tgl dan Waktu Periode'
                elif 'referensi' in col_lower or 'ref' in col_lower:
                    column_mapping[col] = 'No Referensi'
                elif 'deskripsi' in col_lower or 'keterangan' in col_lower:
                    column_mapping[col] = 'Deskripsi'
                elif 'debit' in col_lower or 'db' in col_lower:
                    column_mapping[col] = 'Debit'
                elif 'kredit' in col_lower or 'credit' in col_lower or 'cr' in col_lower:
                    column_mapping[col] = 'Kredit'
                elif 'saldo' in col_lower or 'balance' in col_lower:
                    column_mapping[col] = 'Saldo'
                elif 'no' in col_lower and col_lower.strip() == 'no':
                    column_mapping[col] = 'No.'
            
            if column_mapping:
                df = df.rename(columns=column_mapping)
                return process_bsi_dataframe(df)
            else:
                raise Exception('Excel format does not match BSI structure')
    
    except Exception as e:
        print(f"Error processing BSI Excel: {e}")
        return pd.DataFrame()

def process_bsi_file(filepath, file_ext):
    """
    Main entry point for BSI processor
    Auto-detects format (CSV, PDF, Excel)
    """
    if file_ext == 'csv':
        return process_bsi_csv(filepath)
    elif file_ext == 'pdf':
        return process_bsi_pdf(filepath)
    elif file_ext in ['xlsx', 'xls']:
        return process_bsi_excel(filepath)
    else:
        return pd.DataFrame()
