"""
Organize test_data files into bank-specific folders
"""
import os
import shutil
import fitz  # PyMuPDF

def detect_bank_from_file(filepath):
    """Detect bank type from PDF content"""
    try:
        # Check CSV files first
        if filepath.lower().endswith('.csv'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500).upper()
                if 'MANDIRI' in content:
                    return 'mandiri'
                elif 'BRI' in content:
                    return 'bri'
                elif 'BCA' in content:
                    return 'bca'
                elif 'BNI' in content:
                    return 'bni'
                return 'other'
        
        # For PDFs
        doc = fitz.open(filepath)
        if len(doc) == 0:
            return 'other'
        
        # Read first page
        first_page = doc[0].get_text().upper()
        
        # Check for bank indicators
        if 'KALIMANTAN SELATAN' in first_page or 'KALTRABU' in first_page:
            return 'bank_kalsel'
        elif 'REKENING TAHAPAN' in first_page and 'KCP' in first_page:
            return 'bca'
        elif 'BRIMO' in first_page or 'E-STATEMENTBRIMO' in first_page:
            return 'bri'
        elif 'MANDIRI' in first_page and 'ACCOUNT STATEMENT' in first_page:
            return 'mandiri'
        elif 'BNI' in first_page and ('E-STATEMENT' in first_page or 'STATEMENT' in first_page):
            return 'bni'
        elif 'BANK SYARIAH INDONESIA' in first_page or 'BSI' in first_page:
            return 'bsi'
        elif 'BYOND' in first_page or 'EASY WADIAH' in first_page:
            return 'byond'
        elif 'INFORMASI DEBITUR' in first_page or 'SLIK' in first_page or 'IDEB' in first_page:
            return 'ideb'
        
        doc.close()
        return 'other'
        
    except Exception as e:
        print(f"Error detecting bank for {filepath}: {e}")
        return 'other'

def organize_files():
    """Organize all files in test_data into bank folders"""
    test_data_dir = os.path.join('..', 'test_data')
    
    # Get all files in test_data (not in subdirectories)
    files = [f for f in os.listdir(test_data_dir) 
             if os.path.isfile(os.path.join(test_data_dir, f))]
    
    print(f"Found {len(files)} files to organize\n")
    
    moved_count = {}
    
    for filename in files:
        filepath = os.path.join(test_data_dir, filename)
        
        # Skip if it's a directory
        if os.path.isdir(filepath):
            continue
        
        # Detect bank
        bank = detect_bank_from_file(filepath)
        
        # Create target directory if not exists
        target_dir = os.path.join(test_data_dir, bank)
        os.makedirs(target_dir, exist_ok=True)
        
        # Move file
        target_path = os.path.join(target_dir, filename)
        
        # Check if file already exists in target
        if os.path.exists(target_path):
            print(f"⚠ Skipping {filename} - already exists in {bank}/")
            continue
        
        try:
            shutil.move(filepath, target_path)
            print(f"✓ {filename}")
            print(f"  → {bank}/")
            
            # Track count
            moved_count[bank] = moved_count.get(bank, 0) + 1
        except Exception as e:
            print(f"✗ Error moving {filename}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for bank, count in sorted(moved_count.items()):
        print(f"{bank:15s}: {count} files")
    print(f"\nTotal: {sum(moved_count.values())} files organized")

if __name__ == "__main__":
    print("="*60)
    print("ORGANIZING TEST DATA FILES BY BANK")
    print("="*60)
    print()
    organize_files()
