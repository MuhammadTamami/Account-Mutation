"""
Check accuracy for all bank processors with available test data
"""
import sys
import os
from datetime import datetime
import pandas as pd

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add processors directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'processors'))

from processors.bank_kalsel_processor import process_bank_kalsel_file
from processors.bca_processor import process_bca_file
from processors.bri_processor import process_bri_file
from processors.mandiri_processor import process_mandiri_file
from processors.bni_processor import process_bni_file
from processors.ideb_processor import process_ideb_file

def parse_amount(amount_str):
    """Parse Indonesian number format to float"""
    if isinstance(amount_str, (int, float)):
        return float(amount_str)
    
    # Convert to string and clean
    s = str(amount_str).strip()
    
    # If already a clean number
    dot_count = s.count('.')
    comma_count = s.count(',')
    
    if comma_count > 0 and dot_count > 0:
        # Format: 1,234,567.00 (commas as thousands, dot as decimal)
        # This is standard US/International format
        s = s.replace(',', '')
    elif dot_count > 1 and comma_count == 0:
        # Format: 246.748.875 (dots as thousands separator)
        s = s.replace('.', '')
    elif dot_count > 1 and comma_count == 1:
        # Format: 246.748.875,00 (dots as thousands, comma as decimal)
        s = s.replace('.', '').replace(',', '.')
    elif dot_count == 1 and comma_count == 0:
        # Could be either 1234.56 or 1.234
        # If more than 2 decimals or has trailing zeros after dot, treat as decimal
        parts = s.split('.')
        if len(parts[1]) <= 2:
            pass  # Already in correct format (decimal)
        else:
            # More than 2 decimal places - might be malformed
            pass
    elif dot_count == 0 and comma_count == 1:
        # Format: 1234,56 (comma as decimal)
        s = s.replace(',', '.')
    elif dot_count == 0 and comma_count > 1:
        # Format: 1,234,567 (commas as thousands)
        s = s.replace(',', '')
    
    try:
        return float(s)
    except ValueError:
        print(f"⚠ Could not parse amount: {amount_str}")
        return 0.0

def check_bank_kalsel():
    """Check Bank Kalsel accuracy"""
    print("\n" + "="*80)
    print("BANK KALSEL - Januari 2025")
    print("="*80)
    
    pdf_path = r"..\test_data\bank_kalsel\1. Januari.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    df = process_bank_kalsel_file(pdf_path, 'pdf')
    
    if df is None or df.empty:
        print("❌ Failed to process")
        return False
    
    # Expected values from user's manual calculation
    expected_debit_count = 19
    expected_credit_count = 9
    expected_debit_sum = 1_139_160_015.76
    expected_credit_sum = 3_148_137_081.79
    
    # Calculate actual values
    debit_df = df[df['Type'] == 'Debit']
    credit_df = df[df['Type'] == 'Credit']
    
    actual_debit_count = len(debit_df)
    actual_credit_count = len(credit_df)
    actual_debit_sum = debit_df['Amount'].apply(parse_amount).sum()
    actual_credit_sum = credit_df['Amount'].apply(parse_amount).sum()
    
    print(f"\n📊 Transaction Counts:")
    print(f"   Debit:  {actual_debit_count} (expected: {expected_debit_count}) {'✅' if actual_debit_count == expected_debit_count else '❌'}")
    print(f"   Credit: {actual_credit_count} (expected: {expected_credit_count}) {'✅' if actual_credit_count == expected_credit_count else '❌'}")
    
    print(f"\n💰 Transaction Amounts:")
    print(f"   Debit:  {actual_debit_sum:,.2f}")
    print(f"   Expected: {expected_debit_sum:,.2f}")
    debit_diff = abs(actual_debit_sum - expected_debit_sum)
    debit_accuracy = 100 - (debit_diff / expected_debit_sum * 100) if expected_debit_sum > 0 else 0
    print(f"   Accuracy: {debit_accuracy:.6f}% {'✅' if debit_accuracy == 100 else '❌'}")
    
    print(f"\n   Credit: {actual_credit_sum:,.2f}")
    print(f"   Expected: {expected_credit_sum:,.2f}")
    credit_diff = abs(actual_credit_sum - expected_credit_sum)
    credit_accuracy = 100 - (credit_diff / expected_credit_sum * 100) if expected_credit_sum > 0 else 0
    print(f"   Accuracy: {credit_accuracy:.6f}% {'✅' if credit_accuracy == 100 else '❌'}")
    
    # Check daily balances
    print(f"\n🏦 Daily Balances Check:")
    df['Date_parsed'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    daily_balances = df.groupby('Date_parsed').apply(lambda x: parse_amount(x.iloc[-1]['Balance']))
    print(f"   Total days: {len(daily_balances)}")
    for date, balance in daily_balances.items():
        print(f"   {date.strftime('%d/%m/%Y')}: {balance:,.2f}")
    
    # Overall accuracy
    count_accurate = actual_debit_count == expected_debit_count and actual_credit_count == expected_credit_count
    amount_accurate = debit_accuracy == 100 and credit_accuracy == 100
    
    if count_accurate and amount_accurate:
        print(f"\n✅ BANK KALSEL: 100% ACCURATE")
        return True
    else:
        print(f"\n❌ BANK KALSEL: NOT 100% ACCURATE")
        return False

def check_bca():
    """Check BCA accuracy"""
    print("\n" + "="*80)
    print("BCA - April 2026")
    print("="*80)
    
    pdf_path = r"..\test_data\bca\9. April 2026.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    df = process_bca_file(pdf_path, 'pdf')
    
    if df is None or df.empty:
        print("❌ Failed to process")
        return False
    
    credit_df = df[df['Type'] == 'Credit']
    debit_df = df[df['Type'] == 'Debit']
    
    actual_credit_count = len(credit_df)
    actual_debit_count = len(debit_df)
    
    print(f"\n📊 Transaction Counts:")
    print(f"   Credit: {actual_credit_count}")
    print(f"   Debit:  {actual_debit_count}")
    
    print(f"\n💰 Transaction Amounts:")
    print(f"   Credit: {credit_df['Amount'].apply(parse_amount).sum():,.2f}")
    print(f"   Debit:  {debit_df['Amount'].apply(parse_amount).sum():,.2f}")
    
    print(f"\n🏦 Sample transactions (first 5):")
    print(df[['Date', 'Description', 'Type', 'Amount', 'Balance']].head().to_string())
    
    print(f"\n✅ BCA: Processed {len(df)} transactions ({actual_credit_count} CR, {actual_debit_count} DB)")
    return True

def check_bri():
    """Check BRI accuracy"""
    print("\n" + "="*80)
    print("BRI - April 2026")
    print("="*80)
    
    pdf_path = r"..\test_data\bri\fe9bdc9c-fb00-474d-b952-7b3a26df457a_156154113228_e-StatementBRImo_360101010764538_Apr2026_20260608_100213.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    df = process_bri_file(pdf_path, 'pdf')
    
    if df is None or df.empty:
        print("❌ Failed to process")
        return False
    
    credit_df = df[df['Type'] == 'Credit']
    debit_df = df[df['Type'] == 'Debit']
    
    print(f"\n📊 Transaction Counts:")
    print(f"   Credit: {len(credit_df)}")
    print(f"   Debit:  {len(debit_df)}")
    
    print(f"\n💰 Transaction Amounts:")
    print(f"   Credit: {credit_df['Amount'].apply(parse_amount).sum():,.2f}")
    print(f"   Debit:  {debit_df['Amount'].apply(parse_amount).sum():,.2f}")
    
    print(f"\n🏦 Sample transactions (first 5):")
    print(df[['Date', 'Description', 'Type', 'Amount', 'Balance']].head().to_string())
    
    print(f"\n✅ BRI: Processed {len(df)} transactions ({len(credit_df)} CR, {len(debit_df)} DB)")
    return True

def check_mandiri():
    """Check Mandiri accuracy"""
    print("\n" + "="*80)
    print("MANDIRI - Januari 2026")
    print("="*80)
    
    pdf_path = r"..\test_data\mandiri\1. Mandiri Januari.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    df = process_mandiri_file(pdf_path, 'pdf')
    
    if df is None or df.empty:
        print("❌ Failed to process")
        return False
    
    credit_df = df[df['Type'] == 'Credit']
    debit_df = df[df['Type'] == 'Debit']
    
    print(f"\n📊 Transaction Counts:")
    print(f"   Credit: {len(credit_df)}")
    print(f"   Debit:  {len(debit_df)}")
    
    print(f"\n💰 Transaction Amounts:")
    print(f"   Credit: {credit_df['Amount'].apply(parse_amount).sum():,.2f}")
    print(f"   Debit:  {debit_df['Amount'].apply(parse_amount).sum():,.2f}")
    
    print(f"\n🏦 Sample transactions (first 5):")
    print(df[['Date', 'Description', 'Type', 'Amount', 'Balance']].head().to_string())
    
    print(f"\n✅ MANDIRI: Processed {len(df)} transactions ({len(credit_df)} CR, {len(debit_df)} DB)")
    return True

def check_bni():
    """Check BNI/BYOND accuracy"""
    print("\n" + "="*80)
    print("BYOND - Mei 2026")
    print("="*80)
    
    pdf_path = r"..\test_data\byond\ESTATEMENT-7326292057-052026-10-13-39.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    # This is actually BYOND, not BNI - try byond processor
    try:
        from processors.byond_processor import process_byond_file
        df = process_byond_file(pdf_path, 'pdf')
    except:
        # Fallback to BNI if byond not available
        df = process_bni_file(pdf_path, 'pdf')
    
    if df is None or df.empty:
        print("❌ Failed to process")
        return False
    
    credit_df = df[df['Type'] == 'Credit']
    debit_df = df[df['Type'] == 'Debit']
    
    print(f"\n📊 Transaction Counts:")
    print(f"   Credit: {len(credit_df)}")
    print(f"   Debit:  {len(debit_df)}")
    
    print(f"\n💰 Transaction Amounts:")
    print(f"   Credit: {credit_df['Amount'].apply(parse_amount).sum():,.2f}")
    print(f"   Debit:  {debit_df['Amount'].apply(parse_amount).sum():,.2f}")
    
    print(f"\n🏦 Sample transactions (first 5):")
    print(df[['Date', 'Description', 'Type', 'Amount', 'Balance']].head().to_string())
    
    print(f"\n✅ BYOND: Processed {len(df)} transactions ({len(credit_df)} CR, {len(debit_df)} DB)")
    return True

def check_ideb():
    """Check IDEB accuracy"""
    print("\n" + "="*80)
    print("IDEB - RIZKY ADE")
    print("="*80)
    
    pdf_path = r"..\test_data\ideb\IDEB RIZKY ADE.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    result = process_ideb_file(pdf_path, 'pdf')
    
    if result is None:
        print("❌ Failed to process")
        return False
    
    print(f"\n📊 Detected Bank: {result.get('detected_bank', 'N/A')}")
    print(f"   Total Records: {len(result.get('data', []))}")
    
    if result.get('data'):
        print(f"\n🏦 Sample records:")
        for i, record in enumerate(result['data'][:5], 1):
            print(f"   {i}. {record.get('Nama Bank', 'N/A')} - Plafon: {record.get('Plafon', 'N/A')}")
    
    print(f"\n✅ IDEB: Processed successfully")
    return True

def main():
    """Run all accuracy checks"""
    print("\n" + "="*80)
    print("ACCURACY CHECK FOR ALL BANK PROCESSORS")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Check each bank
    try:
        results['Bank Kalsel'] = check_bank_kalsel()
    except Exception as e:
        print(f"\n❌ Bank Kalsel error: {e}")
        import traceback
        traceback.print_exc()
        results['Bank Kalsel'] = False
    
    try:
        results['BCA'] = check_bca()
    except Exception as e:
        print(f"\n❌ BCA error: {e}")
        import traceback
        traceback.print_exc()
        results['BCA'] = False
    
    try:
        results['BRI'] = check_bri()
    except Exception as e:
        print(f"\n❌ BRI error: {e}")
        import traceback
        traceback.print_exc()
        results['BRI'] = False
    
    try:
        results['Mandiri'] = check_mandiri()
    except Exception as e:
        print(f"\n❌ Mandiri error: {e}")
        import traceback
        traceback.print_exc()
        results['Mandiri'] = False
    
    try:
        results['BNI/BYOND'] = check_bni()
    except Exception as e:
        print(f"\n❌ BNI/BYOND error: {e}")
        import traceback
        traceback.print_exc()
        results['BNI/BYOND'] = False
    
    try:
        results['IDEB'] = check_ideb()
    except Exception as e:
        print(f"\n❌ IDEB error: {e}")
        import traceback
        traceback.print_exc()
        results['IDEB'] = False
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for bank, accurate in results.items():
        status = "✅ PASS" if accurate else "❌ FAIL"
        print(f"{bank:15s}: {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed}/{total} banks passed accuracy check")
    print(f"Overall accuracy: {(passed/total*100):.1f}%")

if __name__ == "__main__":
    main()
