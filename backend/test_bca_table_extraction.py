"""Test BCA table extraction with correct logic"""
import fitz
import re

doc = fitz.open('../test_data/9. April 2026.pdf')

print("Testing BCA table extraction logic")
print("=" * 80)

# Test on a sample page
page = doc[69]  # Page 70 (0-indexed) - near end, has both CR and DB
text = page.get_text()
lines = text.split('\n')

print(f"\nPage 70 sample (last transaction days):")
print("=" * 80)

# Find transactions
in_transaction = False
current_date = None
current_desc = []
current_branch = None
current_mutasi = None
current_saldo = None

for i, line in enumerate(lines):
    # Check for date pattern DD/MM
    date_match = re.match(r'^(\d{2}/\d{2})$', line.strip())
    
    if date_match:
        current_date = date_match.group(1)
        in_transaction = True
        current_desc = []
        current_branch = None
        current_mutasi = None
        current_saldo = None
        continue
    
    if current_date and i < len(lines) - 1:
        # Look for MUTASI column value (amount with optional DB)
        # MUTASI must have decimal point (.) and optional DB suffix
        # Pattern: "1,234,567.89" or "1,234,567.89 DB"
        mutasi_match = re.match(r'^([\d,]+\.\d{2})\s*(DB)?$', line.strip())
        
        if mutasi_match:
            amount = mutasi_match.group(1)
            has_db = mutasi_match.group(2) is not None
            type_str = "DEBIT" if has_db else "CREDIT"
            current_mutasi = f"{amount} ({type_str})"
            
            # Saldo might be next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Saldo pattern: just a number with decimal
                if re.match(r'^[\d,]+\.\d{2}$', next_line):
                    current_saldo = next_line
            
            # Print transaction
            desc = ' '.join(current_desc)
            print(f"\n{current_date}: {desc[:40]:40s}")
            print(f"  Branch: {current_branch if current_branch else 'N/A'}")
            print(f"  Mutasi: {current_mutasi}")
            print(f"  Saldo: {current_saldo if current_saldo else 'N/A'}")
            
            # Reset for next transaction
            current_date = None
            current_desc = []
            continue
        
        # Check for branch (4 digits)
        if re.match(r'^\d{4}$', line.strip()):
            current_branch = line.strip()
            continue
        
        # Check if description
        if line.strip() and not line.strip().startswith(('TANGGAL', 'KETERANGAN', 'CBG', 'MUTASI', 'SALDO', 'Bersambung')):
            # Skip QR/TGH/DDR/MID lines
            if not line.strip().startswith(('QR', 'TGH', 'DDR', 'MID', ':')):
                current_desc.append(line.strip())

doc.close()

print("\n" + "=" * 80)
print("Pattern identified:")
print("=" * 80)
print("1. Date: DD/MM format")
print("2. Description: Multiple lines")
print("3. Branch: 4 digits (optional)")
print("4. MUTASI: amount or 'amount DB'")
print("5. SALDO: standalone amount (optional)")
