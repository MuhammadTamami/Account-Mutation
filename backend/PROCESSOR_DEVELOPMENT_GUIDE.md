# Bank Processor Development Guide

## Overview
Panduan untuk develop atau maintain bank statement processors.

## Core Principles

### 1. Transaction Order Preservation
**ALWAYS** preserve urutan transaksi dari PDF asli:

```python
# ✅ CORRECT - With sequence number
for idx, item in enumerate(output_data):
    item['_sequence'] = idx

df = pd.DataFrame(output_data)
df = df.sort_values(['DateTime', '_sequence']).reset_index(drop=True)
df = df.drop(columns=['_sequence'])
```

```python
# ❌ WRONG - Order becomes random for same datetime
df = pd.DataFrame(output_data)
df = df.sort_values('DateTime').reset_index(drop=True)
```

### 2. Transaction Classification
Gunakan keywords untuk classify Credit vs Debit:

```python
desc_lower = description.lower()

# Credit keywords
if any(kw in desc_lower for kw in ['incoming', 'transfer in', 'skn in', 'rtgs', 'deposit', 'kredit', 'interest', 'bunga']):
    transaction_type = 'Credit'

# Debit keywords  
elif any(kw in desc_lower for kw in ['withdrawal', 'pembayaran', 'transaction fee', 'biaya', 'tax', 'pajak']):
    transaction_type = 'Debit'

# Fallback
else:
    transaction_type = 'Credit' if amount > 0 else 'Debit'
```

### 3. Amount Parsing
Handle berbagai format Indonesian number:

```python
def clean_amount(amount_str):
    """
    Convert Indonesian rupiah format to float
    Supports:
    - 1,234,567.89 (standard)
    - 1234567.89 (no comma)
    - 1,234,567 (no decimal)
    """
    amount_str = str(amount_str).replace('IDR', '').replace('Rp.', '').strip()
    amount_str = amount_str.replace(',', '')  # Remove thousand separator
    try:
        return float(amount_str)
    except:
        return 0.0
```

### 4. Balance Extraction
**Important**: Balance MUST be accurate for daily balance calculation

```python
# Regex for balance (must have decimal)
balance_match = re.search(r'([\d,]+\.[\d]{1,2})$', line)

# Handle edge cases:
# - Balance with 1 decimal: 123.4 → treat as 123.40
# - Balance without decimal: skip or warn
```

### 5. Daily Balance Strategy

Different banks, different strategies:

```python
# BCA: First non-backdate transaction
if 'TANGGAL :' in description:
    # This is backdate, skip for daily balance
    pass

# Bank Kalsel, Mandiri: Last transaction of the day
balance_value = day_transactions.iloc[-1]['Balance']
```

## Testing Checklist

### Before Committing
- [ ] Test with actual PDF file
- [ ] Verify transaction count matches PDF summary
- [ ] Check daily balances are correct
- [ ] Ensure transaction order matches PDF
- [ ] Test with edge cases (same amount, same time)
- [ ] Validate Credit/Debit classification

### Common Issues

#### Issue 1: Transaction Count Mismatch
**Symptom**: Extracted count ≠ PDF summary

**Debug**:
```python
print(f"Expected CR: {expected_cr}, Got: {actual_cr}")
print(f"Expected DB: {expected_db}, Got: {actual_db}")

# Check for:
# 1. SALDO AWAL being counted
# 2. Multi-line transactions counted twice
# 3. Headers being parsed as transactions
```

#### Issue 2: Wrong Transaction Order
**Symptom**: Last transaction not at end

**Fix**: Add sequence number (see Principle #1)

#### Issue 3: Wrong Classification
**Symptom**: Credit counted as Debit or vice versa

**Debug**:
```python
# Print description and classification
for txn in output_data:
    print(f"{txn['Type']:6} | {txn['Description']}")
```

#### Issue 4: Amount Parsing Errors
**Symptom**: Very large or very small amounts

**Debug**:
```python
# Check if reference numbers are being parsed as amounts
if ',' not in amount_str and amount > 100_000_000:
    print(f"⚠️  Possible reference number: {amount_str}")
```

## Bank-Specific Notes

### BCA
- Has backdate transactions (marked with "TANGGAL :")
- Format: Date (DD/MM), Amount (1,234.56 or 1,234.56 DB)
- Daily balance: Use first non-backdate transaction

### Bank Kalsel  
- Format: Date (DD/MM/YYYY), Time (HHMM), Amount, Balance
- Some transactions have amount in first line (IDR Rp. amount IDR Rp.)
- Balance can have 1 or 2 decimal digits
- Special cases need hardcoded fixes for account number as reference

### Mandiri
- Complex multi-line format
- Date includes time (DD/MM/YYYY HH:MM:SS)
- Already has OriginalIndex

### BSI, BRI, Byond
- Already well-implemented with OriginalIndex
- Follow same pattern for new banks

## File Structure

```
processors/
├── bank_detector.py      # Auto-detect bank from PDF
├── bca_processor.py      # BCA
├── bank_kalsel_processor.py  # Bank Kalsel
├── bsi_processor.py      # BSI
├── mandiri_processor.py  # Mandiri
├── bni_processor.py      # BNI
├── bri_processor.py      # BRI
├── byond_processor.py    # Byond
└── ideb_processor.py     # IDEB
```

## Adding New Bank

1. Create `new_bank_processor.py`
2. Implement `process_new_bank_pdf(filepath)`
3. Return DataFrame with columns: Date, Reference, Description, Type, Amount, Balance
4. Add sequence number for order preservation
5. Add to `bank_detector.py`
6. Test with real PDFs
7. Document edge cases

## Best Practices

1. ✅ **Always read PDF first** before parsing
2. ✅ **Print debug info** during development
3. ✅ **Test with multiple PDFs** from same bank
4. ✅ **Handle edge cases** explicitly
5. ✅ **Comment complex logic** 
6. ✅ **Use try-except** for error handling
7. ✅ **Validate against PDF summary** when available
8. ✅ **Preserve original order** with sequence numbers

## Contact
For questions or issues, check:
- `TRANSACTION_ORDER_FIX.md` - Order preservation details
- `FINAL_TEST_RESULTS.md` - Latest test results
- `BANK_KALSEL_FIX_SUMMARY.md` - Bank Kalsel specific fixes
