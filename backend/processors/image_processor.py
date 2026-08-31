"""
Image processor for bank statement images using OCR
Supports: JPG, JPEG, PNG

NOTE: Requires Tesseract OCR to be installed
Download: https://github.com/UB-Mannheim/tesseract/wiki
"""

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
    
    # Configure Tesseract path for Windows
    import os
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe'
    ]
    
    # Find and set Tesseract executable path
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            print(f"Tesseract found at: {path}")
            break
    else:
        print("Warning: Tesseract not found in default locations")
        
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: pytesseract or Pillow not installed. Image processing unavailable.")

import pandas as pd
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert Indonesian number format to float"""
    if not amount_str or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip()
    
    # Remove currency symbols and spaces
    amount_str = amount_str.replace('Rp', '').replace('IDR', '').strip()
    
    # Check if it's zero
    if amount_str in ['0.00', '0,00', '0', '-']:
        return 0.0
    
    # Handle negative sign
    is_negative = amount_str.startswith('-')
    if is_negative:
        amount_str = amount_str[1:]
    
    # Detect format
    if ',' in amount_str and '.' in amount_str:
        last_comma = amount_str.rfind(',')
        last_dot = amount_str.rfind('.')
        
        if last_dot > last_comma:
            # English format: 1,234.56
            amount_str = amount_str.replace(',', '')
        else:
            # Indonesian format: 1.234,56
            amount_str = amount_str.replace('.', '').replace(',', '.')
    elif ',' in amount_str:
        # Only comma
        last_comma_pos = amount_str.rfind(',')
        if len(amount_str) - last_comma_pos <= 3:
            # Decimal separator
            amount_str = amount_str.replace(',', '.')
        else:
            # Thousand separator
            amount_str = amount_str.replace(',', '')
    elif '.' in amount_str:
        # Only dot
        last_dot_pos = amount_str.rfind('.')
        if len(amount_str) - last_dot_pos > 3:
            # Thousand separator
            amount_str = amount_str.replace('.', '')
    
    try:
        value = float(amount_str)
        return -value if is_negative else value
    except:
        return 0.0

def format_indonesian_number(value):
    """Format number as Indonesian format: 1,499,754,00"""
    if pd.isna(value) or value == 0:
        return "0,00"
    
    formatted = f"{value:.2f}"
    parts = formatted.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    integer_with_sep = f"{int(integer_part):,}"
    return f"{integer_with_sep},{decimal_part}"

def extract_text_from_image(filepath):
    """Extract text from image using OCR"""
    if not TESSERACT_AVAILABLE:
        raise Exception("Tesseract OCR not available. Please install pytesseract and Pillow.")
    
    try:
        # Open image
        img = Image.open(filepath)
        
        # Try to use Tesseract
        try:
            # Perform OCR with Indonesian language support
            text = pytesseract.image_to_string(img, lang='eng+ind')
        except pytesseract.TesseractNotFoundError:
            # Fallback to English only
            try:
                text = pytesseract.image_to_string(img, lang='eng')
            except:
                raise Exception("Tesseract executable not found. Please install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki")
        
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from image: {e}")

def extract_summary_from_text(text):
    """Extract total debit/credit summary from image text if available"""
    summary = {
        'total_debit': None,
        'total_credit': None,
        'num_debit': None,
        'num_credit': None
    }
    
    text_lower = text.lower()
    
    # Look for patterns like:
    # "Total Debit: 1,234,567.89"
    # "Dana Keluar: 1.234.567,89"
    # "Jumlah Debit: 10"
    
    # Total debit amount
    debit_patterns = [
        r'total\s+debit[:\s]+([0-9,.]+)',
        r'dana\s+keluar[:\s]+([0-9,.]+)',
        r'total\s+amount\s+debited[:\s]+([0-9,.]+)',
        r'jumlah\s+debit[:\s]+([0-9,.]+)',
        r'total\s+db[:\s]+([0-9,.]+)'
    ]
    
    for pattern in debit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            summary['total_debit'] = clean_amount(match.group(1))
            break
    
    # Total credit amount
    credit_patterns = [
        r'total\s+credit[:\s]+([0-9,.]+)',
        r'dana\s+masuk[:\s]+([0-9,.]+)',
        r'total\s+amount\s+credited[:\s]+([0-9,.]+)',
        r'jumlah\s+kredit[:\s]+([0-9,.]+)',
        r'total\s+cr[:\s]+([0-9,.]+)'
    ]
    
    for pattern in credit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            summary['total_credit'] = clean_amount(match.group(1))
            break
    
    # Number of debit transactions
    num_debit_patterns = [
        r'(?:jumlah|number of|no\.\s+of)\s+debit[:\s]+(\d+)',
        r'debit\s+count[:\s]+(\d+)',
        r'transaksi\s+debit[:\s]+(\d+)'
    ]
    
    for pattern in num_debit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            summary['num_debit'] = int(match.group(1))
            break
    
    # Number of credit transactions
    num_credit_patterns = [
        r'(?:jumlah|number of|no\.\s+of)\s+credit[:\s]+(\d+)',
        r'credit\s+count[:\s]+(\d+)',
        r'transaksi\s+kredit[:\s]+(\d+)'
    ]
    
    for pattern in num_credit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            summary['num_credit'] = int(match.group(1))
            break
    
    # Check if we found any summary info
    has_summary = any(v is not None for v in summary.values())
    
    if has_summary:
        print(f"Found summary in image: Debit={summary['total_debit']}, Credit={summary['total_credit']}")
    
    return summary if has_summary else None

def detect_bank_type(text):
    """Detect bank type from OCR text"""
    text_lower = text.lower()
    
    if 'bsi' in text_lower or 'bank syariah indonesia' in text_lower:
        return 'BSI'
    elif 'mandiri' in text_lower or 'bank mandiri' in text_lower:
        return 'Mandiri'
    else:
        return 'Unknown'
    """Detect bank type from OCR text"""
    text_lower = text.lower()
    
    if 'bsi' in text_lower or 'bank syariah indonesia' in text_lower:
        return 'BSI'
    elif 'mandiri' in text_lower or 'bank mandiri' in text_lower:
        return 'Mandiri'
    else:
        return 'Unknown'

def parse_bsi_transactions_from_text(text):
    """Parse BSI transactions from OCR text"""
    transactions = []
    lines = text.split('\n')
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Try to find date pattern: YYYY-MM-DD or DD/MM/YYYY
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', line)
        
        if date_match:
            date_str = date_match.group(1)
            
            # Extract numbers from line (amounts)
            numbers = re.findall(r'[\d,\.]+', line)
            
            if len(numbers) >= 2:
                # Try to parse as transaction
                try:
                    if '/' in date_str:
                        date = pd.to_datetime(date_str, format='%d/%m/%Y')
                    else:
                        date = pd.to_datetime(date_str)
                    
                    transactions.append({
                        'date': date,
                        'line': line,
                        'numbers': numbers
                    })
                except:
                    continue
    
    return transactions

def parse_mandiri_transactions_from_text(text):
    """Parse Mandiri transactions from OCR text - IMPROVED"""
    transactions = []
    lines = text.split('\n')
    
    # Mandiri e-Statement format patterns
    # Date can be: "1 Jan 2026", "01 Jan 2026", "1Jan2026"
    # Numbers can be: "1,289,000.00", "1289000.00", "-1,289,000.00"
    
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        
        # Look for Mandiri date patterns (more flexible)
        date_patterns = [
            r'(\d{1,2})\s*(\w{3})\s*(\d{4})',  # 1 Jan 2026, 01Jan2026
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # 01/01/2026
            r'(\d{4})-(\d{2})-(\d{2})'  # 2026-01-01
        ]
        
        date_match = None
        for pattern in date_patterns:
            date_match = re.search(pattern, line)
            if date_match:
                break
        
        if date_match:
            # Extract all numbers from this line and next 2 lines (context)
            context = line
            if i + 1 < len(lines):
                context += " " + lines[i + 1]
            if i + 2 < len(lines):
                context += " " + lines[i + 2]
            
            # Find all amounts (with optional minus sign, commas, dots)
            # Pattern: optional minus, digits with optional separators, optional decimal
            amount_pattern = r'-?\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d{1,2})?'
            numbers = re.findall(amount_pattern, context)
            
            # Clean numbers - keep only amounts (> 100)
            cleaned_numbers = []
            for num in numbers:
                try:
                    clean_val = clean_amount(num)
                    if abs(clean_val) >= 100:  # Filter out small numbers (dates, etc)
                        cleaned_numbers.append(num)
                except:
                    continue
            
            if len(cleaned_numbers) >= 2:  # Need at least amount and balance
                try:
                    # Parse date
                    date_str = date_match.group(0)
                    date = None
                    
                    # Try different date formats
                    date_formats = [
                        '%d %b %Y',
                        '%d%b%Y',
                        '%d-%m-%Y',
                        '%d/%m/%Y',
                        '%Y-%m-%d'
                    ]
                    
                    for fmt in date_formats:
                        try:
                            date = pd.to_datetime(date_str, format=fmt)
                            break
                        except:
                            continue
                    
                    if date:
                        transactions.append({
                            'date': date,
                            'line': context[:200],
                            'numbers': cleaned_numbers
                        })
                except Exception as e:
                    continue
    
    print(f"Parsed {len(transactions)} Mandiri transactions")
    return transactions

def process_image_file(filepath):
    """
    Process bank statement image file using OCR
    Returns DataFrame with standardized columns
    
    Raises Exception if Tesseract not installed
    """
    
    if not TESSERACT_AVAILABLE:
        raise Exception("Image processing unavailable: pytesseract or Pillow not installed. Run: pip install pytesseract Pillow")
    
    print(f"Processing image file: {filepath}")
    
    # Extract text from image (will raise exception if Tesseract not found)
    text = extract_text_from_image(filepath)
    
    if not text:
        print("No text extracted from image")
        return pd.DataFrame()
    
    print(f"Extracted {len(text)} characters from image")
    
    # Try to extract summary statistics from image
    summary_info = extract_summary_from_text(text)
    
    # Detect bank type
    bank_type = detect_bank_type(text)
    print(f"Detected bank type: {bank_type}")
    
    # Parse transactions based on bank type
    if bank_type == 'BSI':
        raw_transactions = parse_bsi_transactions_from_text(text)
    elif bank_type == 'Mandiri':
        raw_transactions = parse_mandiri_transactions_from_text(text)
    else:
        print("Unknown bank type, trying generic parsing...")
        raw_transactions = parse_bsi_transactions_from_text(text)
    
    print(f"Found {len(raw_transactions)} potential transactions")
    
    # Convert to standardized format
    output_data = []
    
    for trans in raw_transactions:
        try:
            numbers = trans['numbers']
            
            # For Mandiri: usually format is [amount, balance] or [debit, credit, balance]
            # Amount can be negative (debit)
            
            if len(numbers) >= 2:
                # Parse amounts
                amounts = [clean_amount(n) for n in numbers]
                
                # Last number is usually balance
                balance = amounts[-1]
                
                # Find transaction amount (largest absolute value before balance)
                transaction_amount = 0
                trans_type = 'Credit'
                
                if len(amounts) >= 2:
                    # Check second-to-last for transaction amount
                    potential_amount = amounts[-2]
                    
                    if potential_amount != 0:
                        if potential_amount < 0:
                            trans_type = 'Debit'
                            transaction_amount = abs(potential_amount)
                        else:
                            trans_type = 'Credit'
                            transaction_amount = potential_amount
                    
                    # If still zero, check all amounts for largest
                    if transaction_amount == 0:
                        for amt in amounts[:-1]:  # Exclude balance
                            if abs(amt) > transaction_amount:
                                transaction_amount = abs(amt)
                                trans_type = 'Debit' if amt < 0 else 'Credit'
                
                # Skip if no valid amount
                if transaction_amount == 0:
                    continue
                
                # Extract description from line
                description = trans['line'][:150]
                
                # Clean description - remove numbers
                for num_str in numbers:
                    description = description.replace(num_str, '')
                description = description.strip()
                
                output_data.append({
                    'Date': trans['date'],
                    'Reference': '-',
                    'Description': description if description else 'Transaction',
                    'Type': trans_type,
                    'Amount': format_indonesian_number(transaction_amount),
                    'Balance': format_indonesian_number(balance)
                })
        except Exception as e:
            print(f"Error parsing transaction: {e}")
            continue
    
    if not output_data:
        print("No transactions parsed")
        return pd.DataFrame()
    
    # Create DataFrame
    result_df = pd.DataFrame(output_data)
    result_df = result_df.sort_values('Date').reset_index(drop=True)
    
    # Attach summary info as DataFrame attributes (like Mandiri PDF)
    if summary_info:
        result_df.attrs['ocr_summary'] = summary_info
        print(f"Attached OCR summary to DataFrame")
    
    print(f"Successfully parsed {len(result_df)} transactions")
    
    return result_df
