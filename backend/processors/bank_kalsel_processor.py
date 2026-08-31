"""
Bank Kalsel Processor
Supports Bank Kalimantan Selatan PDF Mutasi Rekening format
"""
import pdfplumber
import pandas as pd
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert Indonesian rupiah format to float
    Bank Kalsel uses format: 246,748,875 or 482,084,174.31
    Comma = thousands separator, Dot = decimal separator (when present)
    """
    if not amount_str or amount_str == '-' or 'Rp.' not in str(amount_str):
        # Check if it's a valid number string
        if not amount_str or amount_str == '-':
            return 0.0
    
    # Remove "Rp." and "IDR Rp."
    amount_str = str(amount_str).replace('IDR Rp.', '').replace('Rp.', '').strip()
    
    if not amount_str:
        return 0.0
    
    # Remove commas (thousand separators)
    # Keep dots (decimal separator)
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

def process_bank_kalsel_pdf(filepath):
    """
    Process Bank Kalsel Mutasi Rekening PDF
    
    Format:
    - Header: Nomor Rekening, Nama, Jenis Produk, Periode Transaksi
    - Table columns: Tanggal, No. Referensi, Keterangan, Debet, Kredit, Saldo
    - Date format: DD/MM/YYYY HHMM
    """
    
    output_data = []
    account_info = {}
    
    try:
        with pdfplumber.open(filepath) as pdf:
            print(f"📄 Processing Bank Kalsel PDF: {len(pdf.pages)} pages")
            
            # Extract account info from first page
            if len(pdf.pages) > 0:
                first_text = pdf.pages[0].extract_text()
                
                if first_text:
                    # Extract account number
                    acc_no_match = re.search(r'Nomor Rekening\s+(\d+)', first_text)
                    if acc_no_match:
                        account_info['accountNumber'] = acc_no_match.group(1)
                    
                    # Extract account name
                    name_match = re.search(r'Nama\s+([A-Z\s]+)', first_text)
                    if name_match:
                        account_info['name'] = name_match.group(1).strip()
                    
                    # Extract product type
                    product_match = re.search(r'Jenis Produk\s+([A-Z\s]+)', first_text)
                    if product_match:
                        account_info['product'] = product_match.group(1).strip()
                    
                    # Extract period
                    period_match = re.search(r'Periode Transaksi\s+(.+)', first_text)
                    if period_match:
                        account_info['period'] = period_match.group(1).strip()
                    
                    if account_info:
                        print(f"✓ Account: {account_info.get('name', '?')} ({account_info.get('accountNumber', '?')})")
            
            # Process all pages
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Clean special characters that might interfere with parsing
                # Replace unicode private use characters
                text = re.sub(r'[\ue000-\uf8ff]', '', text)
                
                lines = text.split('\n')
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Skip empty lines and headers
                    if not line or 'Tanggal' in line or 'Mutasi Rekening' in line or 'Nomor Rekening' in line:
                        i += 1
                        continue
                    
                    # Check if line starts with date pattern: DD/MM/YYYY
                    date_match = re.match(r'^(\d{2}/\d{2}/\d{4})', line)
                    
                    if date_match:
                        try:
                            date_str = date_match.group(1)
                            date = pd.to_datetime(date_str, format='%d/%m/%Y')
                            
                            # Extract rest of line after date
                            rest_of_line = line[date_match.end():].strip()
                            
                            # Extract reference number (format: FT25002ZLD53 or TT250022Q5DT)
                            ref_match = re.search(r'\b([A-Z]{2}\d+[A-Z0-9]*)\b', rest_of_line)
                            reference = ref_match.group(1) if ref_match else '-'
                            
                            # Extract description from current line (after ref, before "IDR Rp.")
                            desc_parts = []
                            if ref_match:
                                desc_after_ref = rest_of_line[ref_match.end():].strip()
                                # Remove "IDR Rp." placeholders
                                desc_after_ref = desc_after_ref.replace('IDR Rp.', '').strip()
                                if desc_after_ref:
                                    desc_parts.append(desc_after_ref)
                            
                            # Look for amounts in NEXT line
                            # Format: HHMM description amount balance
                            # Example: "0845 TRK CC AP HERDIANSYAH 082220055584 246,748,875 482,084,174.31"
                            found_amounts = False
                            time_str = None
                            
                            for j in range(i + 1, min(i + 10, len(lines))):
                                next_line = lines[j].strip()
                                
                                if not next_line:
                                    continue
                                
                                # Stop if we hit another date (next transaction)
                                if re.match(r'^\d{2}/\d{2}/\d{4}', next_line):
                                    break
                                
                                # Look for time pattern at start: HHMM (without requiring space after)
                                time_match = re.match(r'^(\d{4})', next_line)
                                
                                if time_match:
                                    time_str = time_match.group(1)
                                    time_formatted = f"{time_str[:2]}:{time_str[2:]}"
                                    
                                    # Rest of line after time
                                    rest_after_time = next_line[time_match.end():].strip()
                                    
                                    # Look for amounts at end: amount balance
                                    # Format: "... 246,748,875 482,084,174.31" or "... 1,626,832,461 2,108,916,635.31"
                                    # Pattern: space-separated numbers with comma (Indonesian thousands) and optional dot+decimals
                                    amounts_match = re.search(r'([\d,]+(?:\.[\d]{2})?)\s+([\d,]+\.[\d]{2})$', rest_after_time)
                                    
                                    if amounts_match:
                                        amount_str = amounts_match.group(1)
                                        balance_str = amounts_match.group(2)
                                        
                                        # Extract description (between time and amounts)
                                        desc_between = rest_after_time[:amounts_match.start()].strip()
                                        if desc_between:
                                            desc_parts.append(desc_between)
                                        
                                        # Build full description
                                        description = ' '.join(desc_parts).strip()
                                        description = ' '.join(description.split())  # Clean spaces
                                        
                                        # Parse amounts
                                        amount = clean_amount(amount_str)
                                        balance = clean_amount(balance_str)
                                        
                                        # Determine transaction type based on keywords
                                        desc_lower = description.lower()
                                        if any(kw in desc_lower for kw in ['withdrawal', 'pembayaran', 'fee', 'biaya', 'transaction fee']):
                                            transaction_type = 'Debit'
                                        elif any(kw in desc_lower for kw in ['incoming', 'transfer dari', 'deposit', 'kredit']):
                                            transaction_type = 'Credit'
                                        else:
                                            # Default: check if amount is positive (assume credit)
                                            transaction_type = 'Credit' if amount > 0 else 'Debit'
                                        
                                        # Create datetime
                                        datetime_obj = pd.to_datetime(f"{date_str} {time_formatted}", format='%d/%m/%Y %H:%M')
                                        
                                        output_data.append({
                                            'DateTime': datetime_obj,
                                            'Date': date,
                                            'Reference': reference,
                                            'Description': description,
                                            'Type': transaction_type,
                                            'Amount': format_indonesian_number(amount),
                                            'Balance': format_indonesian_number(balance)
                                        })
                                        
                                        found_amounts = True
                                        i = j + 1
                                        break
                                else:
                                    # This is description continuation (no time at start)
                                    # Skip lines that look like additional info
                                    if not next_line.startswith('By cheque') and len(next_line) > 5:
                                        desc_parts.append(next_line)
                            
                            if not found_amounts:
                                i += 1
                        
                        except Exception as e:
                            print(f"⚠ Error parsing line {i}: {e}")
                            i += 1
                            continue
                    else:
                        i += 1
        
        print(f"✓ Extracted {len(output_data)} transactions from Bank Kalsel PDF")
        
        if len(output_data) == 0:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(output_data)
        df = df.sort_values('DateTime').reset_index(drop=True)
        df = df.drop(columns=['DateTime'])
        
        # Attach metadata
        if account_info:
            df.attrs['account_info'] = account_info
        
        return df
    
    except Exception as e:
        print(f"❌ Error processing Bank Kalsel PDF: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def process_bank_kalsel_file(filepath, file_ext):
    """Main entry point for Bank Kalsel processor"""
    if file_ext == 'pdf':
        return process_bank_kalsel_pdf(filepath)
    else:
        print(f"⚠ Bank Kalsel: Unsupported file type .{file_ext}")
        return pd.DataFrame()
