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
    """Format number as International format: 18,000,000.00"""
    if pd.isna(value) or value == 0:
        return "0.00"
    
    # Use standard US locale format (comma for thousands, dot for decimal)
    formatted = f"{value:,.2f}"
    return formatted

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
                            
                            # Check for amount in FIRST line (format: "IDR Rp. amount IDR Rp.")
                            # This happens for some Debit transactions
                            first_line_amount = None
                            first_line_amounts = re.findall(r'IDR Rp\.\s+([\d,]+(?:\.[\d]{2})?)\s+IDR Rp\.', rest_of_line)
                            if first_line_amounts:
                                first_line_amount = clean_amount(first_line_amounts[0])
                            
                            # Extract description from current line (after ref, before "IDR Rp.")
                            desc_parts = []
                            if ref_match:
                                desc_after_ref = rest_of_line[ref_match.end():].strip()
                                # Remove "IDR Rp." placeholders and amounts
                                desc_after_ref = re.sub(r'IDR Rp\.\s+[\d,]+(?:\.[\d]{2})?\s+IDR Rp\.', '', desc_after_ref)
                                desc_after_ref = desc_after_ref.replace('IDR Rp.', '').strip()
                                if desc_after_ref:
                                    desc_parts.append(desc_after_ref)
                            
                            # Also check if reference looks like account number (all digits)
                            # In that case, the text before reference is the description
                            # BUT: Skip this if description looks like a transaction type (Credit Interest, Tax Amount Due, etc.)
                            if reference.isdigit() and len(reference) >= 8:
                                # Text before reference number might be the description
                                before_ref = rest_of_line[:ref_match.start()].strip() if ref_match else ''
                                # Only use it if it's a meaningful description (not empty and not just "IDR Rp.")
                                if before_ref and before_ref != 'IDR Rp.' and len(before_ref) > 5:
                                    # This looks like a real description
                                    desc_parts.insert(0, before_ref)
                            
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
                                    # Format 1: "... 246,748,875 482,084,174.31" (both amount and balance)
                                    # Format 2: "... 920213003627 2,053,637,494.31" (ref number + balance only)
                                    # Pattern: space-separated numbers, balance has decimal (.X or .XX)
                                    # NOTE: Some balances have only 1 decimal digit due to PDF rendering
                                    amounts_match = re.search(r'([\d,]+(?:\.[\d]{1,2})?)\s+([\d,]+\.[\d]{1,2})$', rest_after_time)
                                    
                                    if amounts_match:
                                        potential_amount_str = amounts_match.group(1)
                                        balance_str = amounts_match.group(2)
                                        
                                        # Determine if potential_amount is really an amount or a reference number
                                        # Rules:
                                        # 1. If first line already has amount, this is just balance line
                                        # 2. If number has no comma AND > 100 million, likely a reference
                                        # 3. Real amounts usually have commas for thousands separator
                                        
                                        if first_line_amount is not None:
                                            # Amount already found in first line, use it
                                            amount = first_line_amount
                                            # Skip the potential_amount (it's a reference number)
                                            desc_between = rest_after_time[:amounts_match.start()].strip()
                                        else:
                                            # Check if potential_amount looks like a valid amount
                                            potential_amount_num = clean_amount(potential_amount_str)
                                            
                                            # If no comma and very large (> 100M), it's likely a reference
                                            if ',' not in potential_amount_str and potential_amount_num > 100000000:
                                                # This is a reference number, not an amount - SKIP this transaction line
                                                # Wait for next line that might have proper amount
                                                continue
                                            else:
                                                # This looks like a valid amount
                                                amount = potential_amount_num
                                                desc_between = rest_after_time[:amounts_match.start()].strip()
                                        
                                        # Extract description (between time and amounts)
                                        if desc_between:
                                            desc_parts.append(desc_between)
                                        
                                        # Build full description
                                        description = ' '.join(desc_parts).strip()
                                        description = ' '.join(description.split())  # Clean spaces
                                        
                                        # If description is empty and we have description from first line, use it
                                        if not description and desc_after_ref:
                                            description = desc_after_ref
                                        
                                        # Parse balance
                                        balance = clean_amount(balance_str)                                        # PRIMARY: Balance-based detection (compare with previous transaction)
                                        # This ensures ALL transactions are captured, including fees
                                        if output_data and len(output_data) > 0:
                                            # Get previous balance
                                            prev_balance_str = output_data[-1]['Balance']
                                            # Remove commas and convert to float
                                            prev_balance = float(prev_balance_str.replace(',', ''))
                                            
                                            # Compare: if balance increased = Credit, if decreased = Debit
                                            balance_diff = balance - prev_balance
                                            
                                            if balance_diff > 0:
                                                transaction_type = 'Credit'  # Balance increased
                                            elif balance_diff < 0:
                                                transaction_type = 'Debit'   # Balance decreased
                                            else:
                                                # Balance unchanged (rare), fallback to amount sign
                                                transaction_type = 'Credit' if amount > 0 else 'Debit'
                                        else:
                                            # FALLBACK: For first transaction only, use enhanced keyword detection
                                            desc_lower = description.lower()
                                            
                                            # Credit indicators
                                            credit_keywords = ['incoming', 'transfer in', 'skn in', 'rtgs', 'deposit', 
                                                             'kredit', 'interest', 'bunga', 'pengembalian amount']
                                            
                                            # Debit indicators  
                                            debit_keywords = ['withdrawal', 'pembayaran', 'transaction fee', 'biaya',
                                                            'tax amount', 'pajak', 'admin fee', 'monthly fee',
                                                            'minimum balance fee', 'transfer out']
                                            
                                            if any(kw in desc_lower for kw in credit_keywords):
                                                transaction_type = 'Credit'
                                            elif any(kw in desc_lower for kw in debit_keywords):
                                                transaction_type = 'Debit'
                                            else:
                                                # Last resort: amount sign
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
        
        # Create DataFrame with sequence number to preserve original order
        for idx, item in enumerate(output_data):
            item['_sequence'] = idx
        
        df = pd.DataFrame(output_data)
        df = df.sort_values(['DateTime', '_sequence']).reset_index(drop=True)
        df = df.drop(columns=['DateTime', '_sequence'])
        
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
