"""Test all banks for debit/credit detection accuracy"""
import sys
sys.path.insert(0, 'processors')

from pathlib import Path
from bank_detector import detect_bank
from bsi_processor import process_bsi_file
from bca_processor import process_bca_file
from bri_processor import process_bri_file
from mandiri_processor import process_mandiri_file
from byond_processor import process_byond_file
from bank_kalsel_processor import process_bank_kalsel_file

print("=" * 80)
print("Testing Debit/Credit Detection - All Banks")
print("=" * 80)

test_files = [
    ('uploads/Acc_Statement_0310073771977_2026-06-01_2026-06-30_20260819134418.pdf', 'BANK_KALSEL'),
    ('uploads/9. April 2026.pdf', 'BCA'),
    ('uploads/1. 184399112771_e-StatementBRImo_018001000731560_Jan2026_20260728_110025.pdf', 'BRI'),
    ('uploads/1. Mandiri Januari.pdf', 'MANDIRI'),
    ('uploads/ESTATEMENT-7326292057-052026-10-13-39.pdf', 'BYOND'),
]

for filepath, expected_bank in test_files:
    print(f"\n{'='*80}")
    print(f"File: {Path(filepath).name}")
    print(f"Expected Bank: {expected_bank}")
    print('='*80)
    
    # Detect bank
    detected_bank = detect_bank(filepath, 'pdf')
    
    if detected_bank == 'UNKNOWN':
        print(f"⚠ Detection failed, using expected: {expected_bank}")
        detected_bank = expected_bank
    else:
        print(f"✓ Detected: {detected_bank}")
    
    # Process with correct processor
    try:
        if detected_bank == 'BANK_KALSEL':
            df = process_bank_kalsel_file(filepath, 'pdf')
        elif detected_bank == 'BCA':
            df = process_bca_file(filepath, 'pdf')
        elif detected_bank == 'BRI':
            df = process_bri_file(filepath, 'pdf')
        elif detected_bank in ['MANDIRI', 'MANDIRI_RK']:
            df = process_mandiri_file(filepath, 'pdf')
        elif detected_bank == 'BYOND':
            df = process_byond_file(filepath, 'pdf')
        else:
            print(f"❌ Unknown bank: {detected_bank}")
            continue
        
        if len(df) == 0:
            print(f"❌ No transactions extracted")
            continue
        
        # Summary
        debit_count = len(df[df['Type'] == 'Debit'])
        credit_count = len(df[df['Type'] == 'Credit'])
        
        print(f"\nResults:")
        print(f"  Total transactions: {len(df)}")
        print(f"  Debit: {debit_count} ({debit_count/len(df)*100:.1f}%)")
        print(f"  Credit: {credit_count} ({credit_count/len(df)*100:.1f}%)")
        
        # Look for fee-related transactions
        fee_keywords = ['fee', 'monthly', 'admin', 'biaya', 'tarif', 'charge', 'adm']
        fee_transactions = []
        
        for idx, row in df.iterrows():
            desc_lower = row['Description'].lower()
            if any(keyword in desc_lower for keyword in fee_keywords):
                fee_transactions.append((row['Type'], row['Description'][:60]))
        
        if fee_transactions:
            print(f"\n  Fee-related transactions found: {len(fee_transactions)}")
            for trans_type, desc in fee_transactions[:5]:  # Show first 5
                print(f"    {trans_type:6} | {desc}")
        else:
            print(f"\n  No fee-related transactions found")
        
        # Check for suspicious patterns (all same type)
        if debit_count == 0:
            print(f"  ⚠ WARNING: No debit transactions - might be missing fees!")
        elif credit_count == 0:
            print(f"  ⚠ WARNING: No credit transactions - might be wrong!")
        elif debit_count < len(df) * 0.05:
            print(f"  ⚠ WARNING: Very few debit transactions ({debit_count}/{len(df)}) - check accuracy!")
        
        print(f"\n  ✓ Processing successful")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*80}")
print("Test Complete")
print('='*80)
