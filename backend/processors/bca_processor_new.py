"""
BCA Bank Statement PDF Processor
Clean rewrite with verified simple logic
"""

import pandas as pd
import re


def clean_amount(amount_str):
    """Convert Indonesian number format to float"""
    if pd.isna(amount_str) or amount_str == '' or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip()
    amount_str = amount_str.replace('Rp', '').replace(' ', '').strip()
    amount_str = amount_str.replace('.', '').replace(',', '.')
    
    try:
        return float(amount_str)
    except:
        return 0.0


def format_indonesian_number(value):
    """Format number to Indonesian format with comma separator"""
    if pd.isna(value) or value == 0:
        return "0.00"
    
    formatted = f"{value:,.2f}"
    return formatted


def process_bca_pdf(filepath):
    """
    Process BCA PDF with verified simple logic:
    1. Find date (DD/MM)
    2. Collect description (skip QR/TGH/DDR/MID lines)
    3. Find MUTASI amount (pattern: amount.dd or "amount.dd DB")
    4. Type: Has " DB" = Debit, No " DB" = Credit
    5. Find SALDO (optional, next line after MUTASI)
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("WARNING: PyMuPDF not installed. Install with: pip install PyMuPDF")
        return pd.DataFrame()
    
    try:
        output_data = []
        account_info = {}
        
        doc = fitz.open(filepath)
        print(f"Processing BCA PDF: {len(doc)} pages")
        
        # Extract account info from first page
        if len(doc) > 0:
            first_text = doc[0].get_text()
            lines = first_text.split('\n')
            
            for i, line in enumerate(lines):
                if 'NO. REKENING' in line or 'NO REKENING' in line:
                    if i + 2 < len(lines):
                        acc_no = lines[i + 2].strip().replace(':', '').strip()
                        if acc_no:
                            account_info['accountNumber'] = acc_no
                
                if 'PERIODE' in line:
                    if i + 2 < len(lines):
                        period = lines[i + 2].strip().replace(':', '').strip()
                        if period:
                            account_info['period'] = period
            
            # Find name (before address keywords)
            for i, line in enumerate(lines):
                if line.strip() and len(line.strip()) > 5:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if any(kw in next_line for kw in ['KEC', 'KEL', 'DSN', 'KAB']):
                            name = line.strip()
                            if not any(skip in name for skip in ['REKENING', 'TAHAPAN', 'KCP', 'NO.']):
                                account_info['name'] = name
                                break
            
            if account_info:
                print(f"Account: {account_info.get('name', '?')} ({account_info.get('accountNumber', '?')})")
        
        # Extract summary from last page
        summary = {}
        if len(doc) > 0:
            last_text = doc[-1].get_text()
            last_lines = last_text.split('\n')
            
            for i, line in enumerate(last_lines):
                line_stripped = line.strip()
                
                if line_stripped == 'MUTASI CR':
                    for j in range(i + 1, min(i + 5, len(last_lines))):
                        val = last_lines[j].strip().replace(':', '').strip()
                        if val and ',' in val and '.' in val:
                            summary['mutasi_cr'] = clean_amount(val)
                            for k in range(j + 1, min(j + 3, len(last_lines))):
                                if last_lines[k].strip().isdigit():
                                    summary['count_cr'] = int(last_lines[k].strip())
                                    break
                            break
                
                elif line_stripped == 'MUTASI DB':
                    for j in range(i + 1, min(i + 5, len(last_lines))):
                        val = last_lines[j].strip().replace(':', '').strip()
                        if val and ',' in val and '.' in val:
                            summary['mutasi_db'] = clean_amount(val)
                            for k in range(j + 1, min(j + 3, len(last_lines))):
                                if last_lines[k].strip().isdigit():
                                    summary['count_db'] = int(last_lines[k].strip())
                                    break
                            break
        
        if summary:
            print(f"Summary: CR {summary.get('count_cr', '?')} txns, DB {summary.get('count_db', '?')} txns")
        
        # Get year from period
        year = None
        if 'period' in account_info:
            period_match = re.search(r'(\d{4})', account_info['period'])
            if period_match:
                year = period_match.group(1)
        
        if not year:
            print("WARNING: Could not extract year from period")
            return pd.DataFrame()
        
        # Process all pages for transactions
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            lines = text.split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if not line:
                    i += 1
                    continue
                
                # Skip headers
                if any(kw in line for kw in ['REKENING', 'HALAMAN', 'PERIODE', 'MATA UANG', 'CATATAN', 'Bersambung', 'TANGGAL', 'KETERANGAN', 'CBG', 'MUTASI', 'SALDO']):
                    i += 1
                    continue
                
                # Look for date: DD/MM
                date_match = re.match(r'^(\d{2}/\d{2})$', line)
                
                if date_match:
                    try:
                        date_str = date_match.group(1)
                        date = pd.to_datetime(f"{date_str}/{year}", format='%d/%m/%Y')
                        
                        description_parts = []
                        branch = ''
                        amount = 0.0
                        balance = 0.0
                        transaction_type = None
                        
                        j = i + 1
                        found_mutasi = False
                        
                        while j < min(i + 30, len(lines)):
                            next_line = lines[j].strip()
                            
                            # Stop if hit another date
                            if re.match(r'^\d{2}/\d{2}$', next_line):
                                break
                            
                            if not next_line:
                                j += 1
                                continue
                            
                            # Skip QR/TGH/DDR/MID lines
                            if next_line.startswith(('QR :', 'TGH:', 'DDR:', 'MID :', 'QR:', 'TGH :')):
                                j += 1
                                continue
                            
                            # Check for branch (4 digits only)
                            if re.match(r'^\d{4}$', next_line):
                                branch = next_line
                                j += 1
                                continue
                            
                            # Check for MUTASI (amount with or without " DB")
                            mutasi_match = re.match(r'^([\d,]+\.\d{2})(\s+DB)?$', next_line)
                            
                            if mutasi_match:
                                amount = clean_amount(mutasi_match.group(1))
                                has_db = mutasi_match.group(2) is not None
                                
                                # Type: " DB" = Debit, no " DB" = Credit
                                transaction_type = 'Debit' if has_db else 'Credit'
                                found_mutasi = True
                                
                                # Look for SALDO in next line
                                if j + 1 < len(lines):
                                    saldo_line = lines[j + 1].strip()
                                    if re.match(r'^[\d,]+\.\d{2}$', saldo_line):
                                        balance = clean_amount(saldo_line)
                                
                                break
                            else:
                                # Description line
                                if not next_line.startswith(':') and not (next_line.isdigit() and len(next_line) > 4):
                                    description_parts.append(next_line)
                            
                            j += 1
                        
                        # Add transaction
                        if found_mutasi and transaction_type:
                            description = ' '.join(description_parts).strip()
                            description = ' '.join(description.split())
                            
                            output_data.append({
                                'Date': date,
                                'Reference': branch if branch else '-',
                                'Description': description,
                                'Type': transaction_type,
                                'Amount': format_indonesian_number(amount),
                                'Balance': format_indonesian_number(balance) if balance > 0 else '0.00'
                            })
                        
                        i = j
                    
                    except Exception as e:
                        print(f"WARNING: Error line {i} page {page_num + 1}: {e}")
                        i += 1
                else:
                    i += 1
        
        doc.close()
        
        print(f"Extracted {len(output_data)} transactions")
        
        if len(output_data) == 0:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(output_data)
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Attach metadata
        if account_info:
            df.attrs['account_info'] = account_info
        if summary:
            df.attrs['summary'] = summary
        
        # Validate
        if summary:
            actual_cr = len(df[df['Type'] == 'Credit'])
            actual_db = len(df[df['Type'] == 'Debit'])
            expected_cr = summary.get('count_cr', 0)
            expected_db = summary.get('count_db', 0)
            
            if actual_cr != expected_cr or actual_db != expected_db:
                print(f"Count mismatch: CR {actual_cr}/{expected_cr}, DB {actual_db}/{expected_db}")
            else:
                print(f"Validation PASSED: CR {actual_cr}, DB {actual_db}")
        
        return df
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def process_bca_file(filepath, file_ext):
    """Main entry point"""
    if file_ext == 'pdf':
        return process_bca_pdf(filepath)
    else:
        print(f"BCA only supports PDF format")
        return pd.DataFrame()
