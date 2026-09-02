"""
Mandiri RK OCR Processor
For scanned/CamScanner PDFs of Mandiri Rekening Koran format
Uses Tesseract OCR to extract text from images
"""
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from PIL import Image
import io
import os

# Try to import pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    
    # Set tesseract path for Windows if not in PATH
    import platform
    if platform.system() == 'Windows':
        # Try common installation paths
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✓ Tesseract found at: {path}")
                break
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠ Warning: pytesseract not available. Install with: pip install pytesseract")

# Try to import fitz (PyMuPDF)
try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠ Warning: PyMuPDF not available. Install with: pip install PyMuPDF")

def clean_amount(amount_str):
    """Convert OCR'd amount string to float"""
    if not amount_str or amount_str in ['-', '.00', '00']:
        return 0.0
    
    amount_str = str(amount_str).strip().replace('Rp', '').strip()
    # Remove spaces
    amount_str = amount_str.replace(' ', '')
    # Handle OCR errors: O -> 0, I -> 1, l -> 1
    amount_str = amount_str.replace('O', '0').replace('o', '0')
    amount_str = amount_str.replace('I', '1').replace('l', '1')
    # Remove comma thousand separators
    amount_str = amount_str.replace(',', '')
    
    try:
        return float(amount_str)
    except:
        return 0.0

def format_indonesian_number(value):
    """Format number as Indonesian format (comma as decimal separator)"""
    if pd.isna(value) or value == 0:
        return "0,00"
    
    formatted = f"{value:.2f}"
    parts = formatted.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    # Add thousand separators (dot)
    integer_with_sep = f"{int(integer_part):,}".replace(',', '.')
    return f"{integer_with_sep},{decimal_part}"

def extract_images_from_pdf(filepath):
    """Extract images from PDF file"""
    images = []
    
    if not PYMUPDF_AVAILABLE:
        print("⚠ PyMuPDF not available, cannot extract images")
        return images
    
    try:
        doc = fitz.open(filepath)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get page as image with high resolution for better OCR
            # 300 DPI for good quality
            zoom = 2  # zoom factor (2 = 144 DPI, 3 = 216 DPI, 4 = 288 DPI)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            images.append({
                'page_num': page_num + 1,
                'image': img
            })
            
            print(f"  ✓ Extracted image from page {page_num + 1}: {img.size}")
        
        doc.close()
        return images
        
    except Exception as e:
        print(f"❌ Error extracting images: {e}")
        return images

def ocr_image(img):
    """Perform OCR on image using Tesseract"""
    if not TESSERACT_AVAILABLE:
        raise Exception("Tesseract OCR not available. Please install pytesseract and Tesseract-OCR.")
    
    try:
        # OCR configuration for better accuracy
        # --psm 6: Assume a single uniform block of text
        # --oem 3: Use both legacy and LSTM engines
        custom_config = r'--oem 3 --psm 6'
        
        # Perform OCR
        text = pytesseract.image_to_string(img, lang='eng', config=custom_config)
        
        return text
    except Exception as e:
        print(f"❌ OCR error: {e}")
        return ""

def parse_ocr_text_line(line):
    """
    Parse OCR'd transaction line - handles multiple formats with OCR errors
    
    Format 1 (Mandiri RK): DD/MM/YY DD/MM/YY DESCRIPTION CODE DEBIT CREDIT BALANCE Cr/Dr
    Format 2 (Table format): [NAME] [ACCOUNT] [DATE YYYY-MM-DD] [TIME] [MODE] [DESC] | [AMOUNT] | [BALANCE]
    """
    line = line.strip()
    
    # Skip empty or too short lines
    if not line or len(line) < 30:
        return None
    
    # Skip header lines - more comprehensive
    skip_words = ['NAMA', 'REKENING', 'TANGG', 'TRANS', 'MODE', 'KETERANGAN', 'AMOUNT', 'SALDO', 
                  'DIPINDAI', 'CAMSCANNER', 'PRINTED', 'BRANCH', 'DATE', 'DESCRIPTION', 'CODE', 
                  'DEBIT', 'KREDIT', 'CREDIT', 'BALANCE', 'JENIS']
    if any(word in line.upper() for word in skip_words):
        return None
    
    # Try Format 2 first (table format with dates and pipe separators)
    if '|' in line:
        parts = line.split('|')
        
        # Need at least 2 parts
        if len(parts) >= 2:
            try:
                # Find the part with the largest number (likely balance or amount)
                # Last few parts should contain numbers
                last_3_parts = parts[-3:] if len(parts) >= 3 else parts
                
                # Extract all numbers from last parts
                all_numbers = []
                for part in last_3_parts:
                    # Find numbers (may have dots, commas, spaces)
                    nums = re.findall(r'[\d\s\.,]+', part)
                    for num_str in nums:
                        # Clean and parse
                        clean_num = num_str.replace('.', '').replace(',', '').replace(' ', '')
                        clean_num = clean_num.replace('O', '0').replace('o', '0').replace('I', '1')
                        if len(clean_num) >= 3:  # At least 3 digits
                            try:
                                num_val = float(clean_num)
                                all_numbers.append((num_val, part))
                            except:
                                pass
                
                # Need at least one number (balance)
                if not all_numbers:
                    return None
                
                # Sort by value, largest is likely balance
                all_numbers.sort(reverse=True)
                balance = all_numbers[0][0]
                
                # Second largest (if exists) is likely amount
                if len(all_numbers) >= 2:
                    amount = all_numbers[1][0]
                else:
                    # If only one number, use it as both
                    amount = balance
                
                # Skip if amounts are too small (noise)
                if amount < 100 or balance < 100:
                    return None
                
                # Find date in the line (try multiple formats)
                # Format 1: YYYY-MM-DD or YYYY/MM/DD
                date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', line)
                # Format 2: YYYY MM DD (with spaces - OCR error)
                if not date_match:
                    date_match = re.search(r'(\d{4})\s+(\d{1,2})\s+(\d{1,2})', line)
                    if date_match:
                        date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                        date_match = type('obj', (object,), {'group': lambda self, x: date_str})()
                
                if not date_match:
                    return None
                
                date_str = date_match.group(1).replace('/', '-').replace(' ', '-')
                
                try:
                    trans_date = pd.to_datetime(date_str, format='%Y-%m-%d')
                except:
                    return None
                
                # Extract description
                description = line
                # Remove brackets, numbers, dates, pipes
                description = re.sub(r'\[.*?\]', ' ', description)
                description = re.sub(r'\d{10,}', ' ', description)
                description = re.sub(r'\d{4}[-/\s]\d{1,2}[-/\s]\d{1,2}', ' ', description)
                description = re.sub(r'\d{1,2}:\d{2}:\d{2}', ' ', description)
                description = re.sub(r'[\d\.,]+', ' ', description)
                description = re.sub(r'[|]', ' ', description)
                description = ' '.join(description.split())
                description = description.strip('[]|').strip()
                
                # Clean up common OCR errors in description
                description = description.replace('uo', 'no').replace('ua', 'na')
                
                if not description or len(description) < 3:
                    description = 'Transaction'
                
                # Determine transaction type from keywords
                line_upper = line.upper()
                debit_keywords = ['ANISA', 'AUARANAN', 'WASPINI', 'PBK', 'TRANSFER', 'BAYAR', 'DEBIT', 'KELUAR']
                credit_keywords = ['TERIMA', 'SETORAN', 'DEPOSIT', 'MASUK', 'CREDIT']
                
                if any(word in line_upper for word in debit_keywords):
                    transaction_type = 'Debit'
                elif any(word in line_upper for word in credit_keywords):
                    transaction_type = 'Credit'
                else:
                    # Default: if amount < balance, it's probably debit
                    transaction_type = 'Debit' if amount < balance else 'Credit'
                
                # Try to find reference code
                code_match = re.search(r'(\d{4}/\d{3})', line)
                code = code_match.group(1) if code_match else '-'
                
                return {
                    'Date': trans_date,
                    'Reference': code,
                    'Description': description[:100],
                    'Type': transaction_type,
                    'Amount': format_indonesian_number(amount),
                    'Balance': format_indonesian_number(balance),
                    'BalanceType': 'Cr'
                }
                
            except Exception as e:
                # Failed to parse, continue to next format
                pass
    
    # Try Format 1 (Original Mandiri RK format with DD/MM/YY dates)
    date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})'
    dates = re.findall(date_pattern, line)
    
    if len(dates) >= 2:
        trans_date_str = dates[0]
        
        try:
            trans_date = pd.to_datetime(trans_date_str, format='%d/%m/%y')
        except:
            try:
                trans_date = pd.to_datetime(trans_date_str, format='%d/%m/%Y')
            except:
                return None
        
        # Find numbers
        numbers = re.findall(r'[\d,\.]+', line)
        
        if len(numbers) >= 3:
            debit_str = numbers[-3]
            credit_str = numbers[-2]
            balance_str = numbers[-1]
            
            debit = clean_amount(debit_str)
            credit = clean_amount(credit_str)
            balance = clean_amount(balance_str)
            
            if credit > 0 and debit == 0:
                transaction_type = 'Credit'
                amount = credit
            elif debit > 0 and credit == 0:
                transaction_type = 'Debit'
                amount = debit
            else:
                return None
            
            # Extract description
            desc_part = line
            for num in numbers:
                desc_part = desc_part.replace(num, '')
            desc_part = ' '.join(desc_part.split()).strip()
            
            code_match = re.search(r'(\d{4}/\d{3})', desc_part)
            code = code_match.group(1) if code_match else '-'
            
            return {
                'Date': trans_date,
                'Reference': code,
                'Description': desc_part[:100],
                'Type': transaction_type,
                'Amount': format_indonesian_number(amount),
                'Balance': format_indonesian_number(balance),
                'BalanceType': 'Cr'
            }
    
    return None

def process_mandiri_rk_ocr_pdf(filepath, pdf_password=''):
    """
    Process scanned/CamScanner Mandiri RK PDF using OCR
    """
    
    if not TESSERACT_AVAILABLE:
        raise Exception("Tesseract OCR not available. Install with: pip install pytesseract\nAlso install Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki")
    
    if not PYMUPDF_AVAILABLE:
        raise Exception("PyMuPDF not available. Install with: pip install PyMuPDF")
    
    output_data = []
    account_info = None
    
    print(f"📄 Processing scanned Mandiri RK PDF with OCR...")
    
    # Extract images from PDF
    print(f"📷 Extracting images from PDF...")
    images = extract_images_from_pdf(filepath)
    
    if not images:
        raise Exception("No images found in PDF")
    
    print(f"✓ Found {len(images)} pages")
    
    # Process each page
    for img_data in images:
        page_num = img_data['page_num']
        img = img_data['image']
        
        print(f"\n🔍 OCR processing page {page_num}...")
        
        # Perform OCR
        ocr_text = ocr_image(img)
        
        if not ocr_text or len(ocr_text.strip()) < 50:
            print(f"  ⚠ Minimal text extracted from page {page_num}")
            continue
        
        print(f"  ✓ OCR extracted {len(ocr_text)} characters")
        
        # Extract account info from first page
        if page_num == 1 and not account_info:
            lines = ocr_text.split('\n')
            for i, line in enumerate(lines[:20]):
                # Look for account number pattern
                acc_match = re.search(r'(\d{8}-\d{2}-\d{2}-\d{6}-\d)', line)
                if acc_match:
                    account_info = {
                        'accountNumber': acc_match.group(1)
                    }
                    # Look for name in nearby lines
                    if i > 0:
                        account_info['name'] = lines[i-1].strip()
                    break
        
        # Parse transactions
        lines = ocr_text.split('\n')
        
        for line in lines:
            transaction = parse_ocr_text_line(line)
            if transaction:
                output_data.append(transaction)
        
        print(f"  ✓ Extracted {len([t for t in output_data if 'Date' in t])} transactions so far")
    
    print(f"\n✓ Total extracted: {len(output_data)} transactions")
    
    if len(output_data) == 0:
        print(f"\n❌ No transactions could be parsed from OCR text")
        print(f"⚠  This is a SCANNED PDF with poor OCR quality")
        print(f"⚠  Common OCR issues:")
        print(f"   - Date corruption (e.g., '2025-08 22' instead of '2025-08-22')")
        print(f"   - Number corruption (e.g., 'sopmaceao' instead of amount)")
        print(f"   - Character confusion (I/1, O/0, etc.)")
        print(f"\n✅ SOLUTION: Please request the ORIGINAL PDF file from the bank")
        print(f"   Original bank PDFs are text-based and will parse with 100% accuracy")
        
        # Return None to trigger proper error message
        raise Exception(
            "OCR quality too low - unable to parse transactions. "
            "This is a scanned/CamScanner PDF. "
            "Please request the original PDF file from the bank for 100% accuracy."
        )
    
    # Convert to DataFrame
    df = pd.DataFrame(output_data)
    
    # Sort by date
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Add account info if available
    if account_info:
        df.attrs['account_info'] = account_info
        print(f"✓ Account: {account_info.get('name', '?')} - {account_info.get('accountNumber', '?')}")
    
    return df

def process_mandiri_rk_ocr_file(filepath, file_ext, pdf_password=''):
    """
    Main entry point for Mandiri RK OCR processor
    Currently only supports PDF format
    """
    if file_ext == 'pdf':
        return process_mandiri_rk_ocr_pdf(filepath, pdf_password)
    else:
        raise Exception(f"Mandiri RK OCR processor only supports PDF format, got: {file_ext}")
