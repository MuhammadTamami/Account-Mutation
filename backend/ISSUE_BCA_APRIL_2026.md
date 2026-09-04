# Issue: BCA April 2026 - Extraction Problems

## File
`test_data/9. April 2026.pdf`

## Masalah yang Ditemukan

### 1. Balance Extraction - SEMUA 0.00 ❌
**Current:** Semua balance = 0.00
**Expected:** Balance harus terisi dari PDF

**Root Cause:**
Balance tidak muncul di setiap transaksi, hanya di transaksi tertentu:
```
01/04
KR OTOMATIS 
QR :    7203000.00
DDR:      50421.00
0998
7,152,579.00
261,042,340.31  ← Balance hanya ada di sini!
```

### 2. Transaction Count - Credit Kurang 8 ❌
**Current:** 623 credit
**Expected:** 631 credit (dari PDF summary)
**Difference:** -8 transactions

### 3. Total Amounts - Salah Perhitungan ❌

| Metric | Current Extract | PDF Summary | Difference |
|--------|----------------|-------------|------------|
| Total Credit | 1,532,076,018.21 | 1,880,194,638.18 | -348,118,619.97 |
| Total Debit | 2,093,000,800.99 | 1,822,464,652.25 | +270,536,148.74 |

**Root Cause:** 
1. Type detection salah (Credit jadi Debit atau sebaliknya)
2. Amount extraction salah (mungkin ambil gross instead of net)

## PDF Format Analysis

### Summary Location
Summary ada di **LAST PAGE** (page 71):
```
SALDO AWAL   : 251,746,517.31
MUTASI CR    : 1,880,194,638.18    631
MUTASI DB    : 1,822,464,652.25     34
SALDO AKHIR  : 309,476,503.24
```

### Transaction Format
Ada 2 format amount:
1. **Format 1** (awal bulan): `TGH:` (Tunai/Cash?)
2. **Format 2** (akhir bulan): `QR:` (QR Code payment?)

**Structure:**
```
DD/MM                          ← Date
KR OTOMATIS                    ← Description (Credit indicator)
MID : 885002147087             ← Merchant ID
BHINNIAN SALON AND             ← Merchant name
QR :    4306000.00             ← Gross amount
DDR:          0.00             ← Discount/Deduction
0998                           ← Branch code
4,306,000.00                   ← Net amount (QR - DDR) ← USE THIS!
158,451,771.86                 ← Balance (optional, not always present)
```

### Type Detection
**Credit indicators:**
- Description starts with "KR OTOMATIS" (Kredit Otomatis)
- Description contains "TRSF E-BANKING CR"
- Description contains "CR KOREKSI"
- Description contains "BUNGA" (interest)

**Debit indicators:**
- Amount line ends with "DB"
- Description contains "TRSF E-BANKING DB"
- Description contains "PAJAK"
- Description contains "BIAYA"

## Current BCA Processor Issues

### Issue 1: Amount Extraction
```python
# Current code looks for amount pattern
amount_match = re.search(r'([\d,]+\.\d{2})', next_line)
```

**Problem:** Ini akan match QR/TGH amount (gross), bukan net amount!

**Solution:** 
1. Extract QR/TGH amount AND DDR
2. Calculate net = QR/TGH - DDR
3. Or directly use net amount line (line after branch code)

### Issue 2: Balance Extraction
```python
# Current code only checks next line
balance_match = re.search(r'([\d,]+\.\d{2})', remainder)
if not balance_match:
    # Check next line
    balance_match = re.match(r'^([\d,]+\.\d{2})$', next_next)
```

**Problem:** Balance bisa beberapa lines setelah amount!

**Solution:** Look ahead up to 5 lines untuk balance pattern

### Issue 3: Type Detection
```python
# Current code hanya check keywords di description
if 'TRSF' in desc_text or 'TARIKAN' in desc_text:
    transaction_type = 'Debit'
else:
    transaction_type = 'Credit'
```

**Problem:** 
1. Terlalu simple, banyak false positive/negative
2. Tidak check "DB" suffix di amount line
3. Tidak check "KR OTOMATIS" pattern

**Solution:**
1. Check amount line untuk "DB" suffix
2. Check description untuk clear indicators:
   - Credit: "KR OTOMATIS", "TRSF.*CR", "CR KOREKSI", "BUNGA"
   - Debit: "TRSF.*DB", "PAJAK", "BIAYA", "TARIKAN"
3. Default to Credit if "KR OTOMATIS", otherwise check keywords

## Recommended Fix Strategy

### Phase 1: Quick Fixes
1. ✅ Extract and validate against PDF summary (last page)
2. ✅ Improve type detection with DB suffix check
3. ✅ Fix amount extraction to use net amount

### Phase 2: Comprehensive Refactor
1. Rewrite BCA processor to handle multiple format variations
2. Add table detection using PyMuPDF table extraction
3. Implement proper state machine for transaction parsing
4. Add validation against summary for all metrics

## Testing
```bash
cd backend
python test_bca_april.py  # Current test shows issues
```

## Expected Output After Fix
```
Total records: 665 (631 + 34)
Credit transactions: 631 ✓
Debit transactions: 34 ✓
Total Credit: Rp 1,880,194,638.18 ✓
Total Debit: Rp 1,822,464,652.25 ✓
Balance: Non-zero for transactions that have balance ✓
```

## Priority
**HIGH** - This affects data accuracy significantly
- Wrong totals can cause reconciliation issues
- Missing transactions (8 credits) is critical
- Zero balances break daily balance feature

## Notes
BCA format is the most complex among all banks due to:
- Multi-line transaction format
- Variable amount indicators (TGH, QR)
- Optional balance field
- No clear DB/CR column
- Mixed formats within same PDF

Consider recommending users to export CSV from BCA internet banking instead of parsing PDF for better accuracy.
