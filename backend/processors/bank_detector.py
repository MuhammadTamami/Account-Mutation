"""
Smart Bank Detector
Detects bank type from file content, not just file extension
"""
import pandas as pd
import pdfplumber
import re

def detect_bank_from_csv(filepath):
    """Detect bank from CSV file content"""
    try:
        # Read first few lines
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # First 1000 chars
        
        content_lower = content.lower()
        
        #BYOND Patterns
        if 'byond' in content_lower:
            return 'BYOND'
        if 'detail transaksi' in content_lower and 'no reff' in content_lower:
            return 'BYOND'
        if 'easy wadiah' in content_lower and 'laporan rekening' in content_lower:
            return 'BYOND'

        # BSI patterns
        if 'bsi' in content_lower or 'bank syariah indonesia' in content_lower:
            return 'BSI'
        
        # Check column headers
        if 'tgl dan waktu periode' in content_lower and 'd/k' in content_lower:
            return 'BSI'
        
        # BCA patterns
        if 'bca' in content_lower or 'bank central asia' in content_lower:
            return 'BCA'
        
        # BRI patterns
        if 'bri' in content_lower or 'bank rakyat indonesia' in content_lower:
            return 'BRI'
        
        # BNI patterns
        if 'bni' in content_lower or 'bank negara indonesia' in content_lower:
            return 'BNI'
        
        # Mandiri patterns (CSV format)
        if 'mandiri' in content_lower or 'bank mandiri' in content_lower:
            return 'MANDIRI'
        
        # Default: try to detect from structure
        # BSI has these columns: "Tgl dan Waktu Periode","No Referensi","Deskripsi","Kode","D/K","Debit","Kredit","Saldo"
        if 'no referensi' in content_lower and 'deskripsi' in content_lower and 'debit' in content_lower and 'kredit' in content_lower:
            return 'BSI'
        
        return 'UNKNOWN'
    
    except Exception as e:
        print(f"Error detecting bank from CSV: {e}")
        return 'UNKNOWN'

def detect_bank_from_pdf(filepath):
    """Detect bank from PDF file content - handles password-protected PDFs"""
    try:
        # Try pdfplumber first
        text = None
        text_lower = None
        
        try:
            # Try to open PDF - first without password, then with common passwords
            passwords_to_try = ['', '07031985']  # Empty first, then default Mandiri password
            
            pdf = None
            pdf_opened = False
            
            for pwd in passwords_to_try:
                try:
                    pdf = pdfplumber.open(filepath, password=pwd)
                    _ = len(pdf.pages)  # Test if we can access pages
                    pdf_opened = True
                    break
                except Exception:
                    if pdf:
                        pdf.close()
                    pdf = None
                    continue
            
            if pdf_opened and pdf is not None:
                try:
                    if len(pdf.pages) > 0:
                        # Read first page
                        first_page = pdf.pages[0]
                        text = first_page.extract_text()
                        
                        if not text:
                            # Try second page if first page has no text
                            if len(pdf.pages) > 1:
                                text = pdf.pages[1].extract_text()
                finally:
                    if pdf:
                        pdf.close()
        except Exception as e:
            print(f"⚠ pdfplumber failed: {e}")
        
        # If pdfplumber failed, try PyMuPDF
        if not text:
            print(f"⚠ pdfplumber failed, trying PyMuPDF...")
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(filepath)
                if len(doc) > 0:
                    text = doc[0].get_text()
                    if not text and len(doc) > 1:
                        text = doc[1].get_text()
                doc.close()
                print(f"✓ PyMuPDF successfully extracted text")
            except Exception as e:
                print(f"⚠ PyMuPDF also failed: {e}")
        
        if not text:
            print(f"⚠ Could not extract text from PDF: {filepath}")
            return 'UNKNOWN'
        
        text_lower = text.lower()
        print(f"📄 PDF text sample (first 200 chars): {text_lower[:200]}")
        
        # IDEB SLIK patterns - CHECK FIRST (contains many bank names, can be misdetected)
        if 'ideb' in text_lower or 'sistem layanan informasi keuangan' in text_lower:
            print(f"✓ Detected: IDEB (found 'ideb' or 'sistem layanan informasi keuangan')")
            return 'IDEB'
        if 'informasi debitur' in text_lower and 'baki debet' in text_lower and 'plafon awal' in text_lower:
            print(f"✓ Detected: IDEB (found SLIK pattern)")
            return 'IDEB'
        
        # Mandiri patterns - CHECK AFTER IDEB (before BRI check)
        # Pattern 1: Mandiri e-Statement format (has both "e-statement" AND "menara mandiri")
        if 'e-statement' in text_lower and 'menara mandiri' in text_lower:
            print(f"✓ Detected: MANDIRI (found 'e-statement' + 'menara mandiri')")
            return 'MANDIRI'
        # Pattern 2: Account Statement format
        if 'account statement' in text_lower and 'posting date' in text_lower:
            print(f"✓ Detected: MANDIRI (found 'account statement' + 'posting date')")
            return 'MANDIRI'
        
        # BRI patterns - CHECK AFTER Mandiri e-Statement
        if 'brimo' in text_lower:
            print(f"✓ Detected: BRI (found 'brimo')")
            return 'BRI'
        # Only check for "e-statement" if NOT Mandiri (no "menara mandiri")
        if 'e-statement' in text_lower.replace(' ', '') and 'menara mandiri' not in text_lower:
            print(f"✓ Detected: BRI (found 'e-statement' without 'menara mandiri')")
            return 'BRI'
        if 'laporan transaksi finansial' in text_lower and 'britama' in text_lower:
            print(f"✓ Detected: BRI (found 'laporan transaksi finansial' + 'britama')")
            return 'BRI'
        if 'laporan transaksi finansial' in text_lower and 'bri' in text_lower:
            print(f"✓ Detected: BRI (found 'laporan transaksi finansial' + 'bri')")
            return 'BRI'
        # Generic BRI check - but must not be in transaction description
        if 'bank rakyat indonesia' in text_lower:
            print(f"✓ Detected: BRI (found 'bank rakyat indonesia')")
            return 'BRI'
        
        # Mandiri generic patterns - CHECK AFTER BRI
        # Pattern 3: Generic Mandiri check
        if 'mandiri' in text_lower or 'bank mandiri' in text_lower:
            # Extra check: Make sure it's not just a BRI file with "mandiri" in transactions
            if 'britama' not in text_lower and 'laporan transaksi finansial' not in text_lower:
                print(f"✓ Detected: MANDIRI (found 'mandiri' in text)")
                return 'MANDIRI'
        
        # BCA patterns
        if 'bca' in text_lower or 'bank central asia' in text_lower:
            print(f"✓ Detected: BCA")
            return 'BCA'
        # BCA Rekening Tahapan format
        if 'rekening tahapan' in text_lower and 'kcp' in text_lower:
            print(f"✓ Detected: BCA (found 'rekening tahapan')")
            return 'BCA'
        if 'keterangan' in text_lower and 'mutasi' in text_lower and 'cbg' in text_lower:
            print(f"✓ Detected: BCA (found tabular format)")
            return 'BCA'
        
        # BNI patterns
        if 'bni' in text_lower or 'bank negara indonesia' in text_lower:
            print(f"✓ Detected: BNI")
            return 'BNI'
        # BNI TRANSACTION INQUIRY format
        if 'transaction inquiry' in text_lower and 'account' in text_lower and 'post date' in text_lower:
            print(f"✓ Detected: BNI (found 'transaction inquiry')")
            return 'BNI'
        
        # Bank Kalsel patterns
        if 'bank kalsel' in text_lower or 'bank kalimantan selatan' in text_lower:
            print(f"✓ Detected: BANK_KALSEL")
            return 'BANK_KALSEL'
        if 'mutasi rekening' in text_lower and 'jenis produk' in text_lower:
            print(f"✓ Detected: BANK_KALSEL (found 'mutasi rekening')")
            return 'BANK_KALSEL'
        
        # BSI patterns
        if 'bsi' in text_lower or 'bank syariah indonesia' in text_lower:
            print(f"✓ Detected: BSI")
            return 'BSI'
        
        # Check for common rekening koran patterns
        if 'rekening koran' in text_lower or 'mutasi rekening' in text_lower:
            print(f"⚠ Found 'rekening koran' but couldn't detect specific bank")
            # Try to detect from structure/numbers
            # If has debit/kredit columns, assume it's a generic format
            if 'debit' in text_lower and 'kredit' in text_lower:
                print(f"ℹ Found debit/kredit columns, trying BSI format as fallback")
                return 'BSI'  # Try BSI format as it's most common
        
        print(f"⚠ Could not detect bank from PDF: {filepath}")
        return 'UNKNOWN'
    
    except Exception as e:
        print(f"❌ Error detecting bank from PDF: {e}")
        import traceback
        traceback.print_exc()
        return 'UNKNOWN'

def detect_bank_from_excel(filepath):
    """Detect bank from Excel file content"""
    try:
        # Try to read first sheet
        df = pd.read_excel(filepath, nrows=10)
        
        # Convert to string for searching
        content = df.to_string().lower()
        
        # BSI patterns
        if 'bsi' in content or 'bank syariah indonesia' in content:
            return 'BSI'
        
        # BCA patterns
        if 'bca' in content or 'bank central asia' in content:
            return 'BCA'
        
        # BRI patterns
        if 'bri' in content or 'bank rakyat indonesia' in content:
            return 'BRI'
        
        # BNI patterns
        if 'bni' in content or 'bank negara indonesia' in content:
            return 'BNI'
        
        # Mandiri patterns
        if 'mandiri' in content or 'bank mandiri' in content:
            return 'MANDIRI'
        
        # Check column names
        columns = [col.lower() for col in df.columns]
        
        # BSI column pattern
        if 'tgl dan waktu periode' in ' '.join(columns) or ('debit' in columns and 'kredit' in columns and 'd/k' in ' '.join(columns)):
            return 'BSI'
        
        return 'UNKNOWN'
    
    except Exception as e:
        print(f"Error detecting bank from Excel: {e}")
        return 'UNKNOWN'

def detect_bank(filepath, file_ext):
    """
    Smart bank detection from file content
    
    Args:
        filepath: Path to file
        file_ext: File extension (csv, pdf, xlsx, etc.)
    
    Returns:
        Bank name (BSI, MANDIRI, BCA, BRI, BNI, UNKNOWN)
    """
    
    if file_ext == 'csv':
        return detect_bank_from_csv(filepath)
    elif file_ext == 'pdf':
        return detect_bank_from_pdf(filepath)
    elif file_ext in ['xlsx', 'xls']:
        return detect_bank_from_excel(filepath)
    else:
        return 'UNKNOWN'
