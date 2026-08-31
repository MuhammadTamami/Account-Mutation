"""
IDEB SLIK Processor
Extract credit/loan data from IDEB SLIK PDF
"""
import pandas as pd
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert Indonesian number format to float"""
    if pd.isna(amount_str) or amount_str == '' or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip()
    
    # Remove "Rp" and spaces
    amount_str = amount_str.replace('Rp', '').replace(' ', '').strip()
    
    # Indonesian format: 1.234.567,89 (dot=thousand, comma=decimal)
    # Remove dots (thousand separator)
    amount_str = amount_str.replace('.', '')
    # Replace comma with dot for decimal
    amount_str = amount_str.replace(',', '.')
    
    try:
        return float(amount_str)
    except:
        return 0.0

def format_number_all_commas(value):
    """
    Format number with commas for both thousand separator and decimal separator
    Example: 337,313,654,34 (all commas)
    """
    if pd.isna(value) or value == 0:
        return "0,00"
    
    # Format with comma as thousand separator and dot as decimal
    formatted = f"{value:,.2f}"
    # Replace dot with comma for decimal
    formatted = formatted.replace('.', ',')
    
    return formatted

def parse_date(date_str):
    """Parse date from various formats"""
    if not date_str or pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    # Month mapping Indonesian -> English
    month_map = {
        'Januari': 'January', 'Februari': 'February', 'Maret': 'March',
        'April': 'April', 'Mei': 'May', 'Juni': 'June',
        'Juli': 'July', 'Agustus': 'August', 'September': 'September',
        'Oktober': 'October', 'November': 'November', 'Desember': 'December'
    }
    
    # Replace Indonesian month names
    for ind, eng in month_map.items():
        date_str = date_str.replace(ind, eng)
    
    # Try various formats
    formats = [
        '%d %B %Y',      # 16 December 2021
        '%d %b %Y',      # 16 Dec 2021
        '%d-%m-%Y',      # 16-12-2021
        '%d/%m/%Y',      # 16/12/2021
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None

def format_date_mmddyyyy(date_obj):
    """Format datetime object to mm/dd/yyyy string for Excel"""
    if not date_obj or pd.isna(date_obj):
        return ''
    
    try:
        if isinstance(date_obj, str):
            date_obj = parse_date(date_obj)
        
        if date_obj:
            return date_obj.strftime('%m/%d/%Y')
    except:
        pass
    
    return ''

def calculate_months_difference(start_date, end_date):
    """Calculate months difference between two dates"""
    if not start_date or not end_date:
        return 0
    
    years = end_date.year - start_date.year
    months = end_date.month - start_date.month
    
    total_months = years * 12 + months
    
    return total_months

def extract_kualitas_number(kualitas_str):
    """Extract number from Kualitas string (e.g., '1 - Lancar' -> '1')"""
    if not kualitas_str or pd.isna(kualitas_str):
        return ''
    
    kualitas_str = str(kualitas_str).strip()
    
    # Extract first number
    match = re.match(r'^(\d+)', kualitas_str)
    if match:
        return match.group(1)
    
    return ''

def process_ideb_pdf(filepath):
    """
    Process IDEB SLIK PDF and extract credit data where Baki Debet > 0
    
    Returns DataFrame with columns:
    - Nama Bank (from Pelapor)
    - Plafon (from Plafon Awal)
    - Yield (from Suku Bunga/Imbalan)
    - O/S (from Baki Debet)
    - Tanggal Pencairan (from Tanggal Mulai)
    - Tanggal Jatuh Tempo (from Tanggal Jatuh Tempo)
    - Jk Waktu (calculated in months)
    - Kol (from Kualitas, number only)
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(f"⚠ PyMuPDF not installed. Install with: pip install PyMuPDF")
        return pd.DataFrame()
    
    try:
        output_data = []
        
        doc = fitz.open(filepath)
        print(f"📄 Processing IDEB SLIK PDF: {len(doc)} pages")
        
        # Extract all text
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        
        doc.close()
        
        # Split into credit entries
        # Pattern 1: "Kredit/Pembiayaan Pelapor" (most common)
        # Pattern 2: "Pelapor" at start of line (for nested entries)
        # We need to handle both patterns
        
        # First, mark all split points
        import re
        
        # Find all "Kredit/Pembiayaan Pelapor" positions
        pattern1 = r'Kredit/Pembiayaan\s+Pelapor'
        # Find all standalone "Pelapor" at line start (not preceded by "Kredit/Pembiayaan")
        pattern2 = r'(?<!\w)Pelapor\s*\n\s*Cabang\s*\n\s*Baki Debet'
        
        # Use pattern1 as primary split, but also handle pattern2
        entries = re.split(pattern1, full_text)
        
        print(f"Found {len(entries)} potential entries (pattern 1)")
        
        # Now for each entry, check if it contains nested entries (pattern2)
        all_entries = []
        for entry in entries:
            # Split by standalone Pelapor pattern
            sub_entries = re.split(pattern2, entry)
            if len(sub_entries) > 1:
                # This entry contains nested entries
                # Add "Pelapor\nCabang\nBaki Debet" back to each sub-entry (except first)
                for i, sub_entry in enumerate(sub_entries):
                    if i == 0:
                        all_entries.append(sub_entry)
                    else:
                        # Prepend the split pattern
                        all_entries.append("Pelapor\nCabang\nBaki Debet" + sub_entry)
            else:
                all_entries.append(entry)
        
        print(f"After sub-splitting: {len(all_entries)} total entries")
        
        for entry in all_entries[1:]:  # Skip first split (before first entry)
            try:
                # Extract Pelapor (Bank Name)
                # After split, the bank name appears after "Tanggal Update" line
                # Pattern: ...Tanggal Update\n[BANK NAME]\n...
                pelapor_match = re.search(r'Tanggal Update\s*\n([^\n]+)', entry)
                if pelapor_match:
                    pelapor = pelapor_match.group(1).strip()
                else:
                    # Fallback: get first non-empty line
                    lines = [l.strip() for l in entry.split('\n') if l.strip()]
                    pelapor = lines[3] if len(lines) > 3 else ''  # Usually 4th line
                
                # Clean pelapor - remove numbers/codes at start (e.g., "122 - ")
                pelapor = re.sub(r'^\d+\s*-\s*', '', pelapor)
                
                # Extract Baki Debet (must be > 0)
                # Format can vary:
                # - Same line: "Baki Debet Rp 1.234,56"
                # - Separate lines: "Baki Debet\nTanggal Update\n...\nRp 1.234,56"
                
                baki_match = re.search(r'Baki Debet\s+Rp\s+([\d.,]+)', entry)
                if not baki_match:
                    # Try alternate format: Baki Debet on one line, amount on next section
                    # Look for "Baki Debet" followed by newlines and eventually "Rp amount"
                    baki_match = re.search(r'Baki Debet[\s\S]{0,200}?Rp\s+([\d.,]+)', entry)
                
                if not baki_match:
                    continue
                
                baki_debet = clean_amount(baki_match.group(1))
                
                # Skip if Baki Debet is 0
                if baki_debet <= 0:
                    continue
                
                # Extract Plafon Awal
                plafon_match = re.search(r'Plafon Awal\s+Rp\s+([\d.,]+)', entry)
                plafon_awal = clean_amount(plafon_match.group(1)) if plafon_match else 0.0
                
                # Extract Suku Bunga/Imbalan (Yield)
                bunga_match = re.search(r'Suku Bunga/Imbalan\s+([\d,.]+)\s*%', entry)
                suku_bunga = bunga_match.group(1).replace(',', '.') if bunga_match else '0'
                
                # Extract Tanggal Mulai (Tanggal Pencairan)
                tgl_mulai_match = re.search(r'Tanggal Mulai\s+(\d{1,2}\s+\w+\s+\d{4})', entry)
                tgl_pencairan_str = tgl_mulai_match.group(1) if tgl_mulai_match else ''
                tgl_pencairan = parse_date(tgl_pencairan_str)
                
                # Extract Tanggal Jatuh Tempo
                tgl_tempo_match = re.search(r'Tanggal Jatuh Tempo\s+(\d{1,2}\s+\w+\s+\d{4})', entry)
                tgl_jatuh_tempo_str = tgl_tempo_match.group(1) if tgl_tempo_match else ''
                tgl_jatuh_tempo = parse_date(tgl_jatuh_tempo_str)
                
                # Calculate Jangka Waktu (in months)
                jk_waktu = calculate_months_difference(tgl_pencairan, tgl_jatuh_tempo) if tgl_pencairan and tgl_jatuh_tempo else 0
                
                # Extract Kualitas (Kol)
                kualitas_match = re.search(r'Kualitas\s+(\d+\s*-\s*\w+)', entry)
                kualitas_str = kualitas_match.group(1) if kualitas_match else ''
                kol = extract_kualitas_number(kualitas_str)
                
                # Format dates as mm/dd/yyyy for Excel
                tgl_pencairan_formatted = format_date_mmddyyyy(tgl_pencairan)
                tgl_jatuh_tempo_formatted = format_date_mmddyyyy(tgl_jatuh_tempo)
                
                # Add to output
                output_data.append({
                    'Nama Bank': pelapor,
                    'Plafon': format_number_all_commas(plafon_awal),
                    'Yield (%)': suku_bunga,
                    'O/S': format_number_all_commas(baki_debet),
                    'Tanggal Pencairan': tgl_pencairan_formatted,
                    'Tanggal Jatuh Tempo': tgl_jatuh_tempo_formatted,
                    'Jk Waktu': jk_waktu,
                    'Kol': kol
                })
                
                print(f"✓ Extracted: {pelapor} - Baki Debet: {format_number_all_commas(baki_debet)}")
            
            except Exception as e:
                print(f"⚠ Error parsing entry: {e}")
                continue
        
        print(f"\n✓ Extracted {len(output_data)} credits with Baki Debet > 0")
        
        if len(output_data) == 0:
            print(f"⚠ No credits found with Baki Debet > 0")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(output_data)
        
        return df
    
    except Exception as e:
        print(f"❌ Error processing IDEB PDF: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def process_ideb_file(filepath, file_ext):
    """
    Main entry point for IDEB processor
    Only supports PDF format
    """
    if file_ext == 'pdf':
        return process_ideb_pdf(filepath)
    else:
        print(f"⚠ IDEB only supports PDF format")
        return pd.DataFrame()
