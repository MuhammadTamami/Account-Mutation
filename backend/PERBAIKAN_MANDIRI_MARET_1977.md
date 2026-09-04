# Perbaikan Mandiri Parser - Missing Transactions in Page 5

## Masalah Awal
File `acct_1977_Maret 2026.pdf` tidak mendeteksi semua transaksi dengan benar:
- **Credit: 23** (expected 24) ❌
- **Debit: 53** (expected 53) ✓

## Masalah Setelah Fix Pertama
Setelah fix untuk credit, debit malah jadi salah:
- **Credit: 24** (expected 24) ✓
- **Debit: 52** (expected 53) ❌

## Investigasi Lengkap

### PDF Summary (halaman 1)
```
No. of Credit: 24
No. of Debit: 53
Total: 77
```

### Transaksi yang Hilang
Di **halaman 5** (halaman terakhir), ada **DUA transaksi** yang tidak terdeteksi:
1. **Bunga** (Credit): Rp 159,475.25
2. **Pajak** (Debit): Rp 31,895.05

### Structure Page 5
```
Line 0: Account Statement (header)
Line 1: Created 30 Jun 2026 10:56:41 (header)
Line 2: 00 Bunga 03101 - 0.00 159,475.25 295,162,850.73  ← CREDIT (amounts BEFORE date)
Line 3: 31/03/2026 23:59:                                  ← SHARED DATE for BOTH!
Line 4: Pajak 03101 - 31,895.05 0.00 295,130,955.68       ← DEBIT (amounts AFTER date)
Line 5: 00 (row number)
Line 6: For further questions... (footer)
```

## Akar Masalah

**DUA transaksi berbagi SATU date line dengan format yang BERBEDA dari format normal:**

**Format Normal** (halaman 1-4):
```
31/03/2026 23:59:                    ← Date first
Bunga 03101 - 0.00 159,475.25 ...   ← Then amounts
```

**Format Page 5** (edge case):
```
Bunga 03101 - 0.00 159,475.25 ...   ← Amounts BEFORE date (transaction 1)
31/03/2026 23:59:                    ← Shared DATE
Pajak 03101 - 31,895.05 0.00 ...    ← Amounts AFTER date (transaction 2)
```

### Timeline Perbaikan

**Fix #1** (hanya handled credit):
- Tambah logic untuk check **PREVIOUS line** saja
- Result: Credit ✓ (24), Debit ✗ (52)
- Masalah: Tidak check NEXT line, jadi Pajak tidak terdeteksi

**Fix #2** (handled both):
- Update logic untuk check **BOTH previous AND next lines**
- Check previous line untuk transaksi sebelum date (Bunga)
- Check next line untuk transaksi setelah date (Pajak)
- Extract kedua transaksi dengan date yang sama

## Solusi Final

Update `mandiri_processor.py` untuk handle multiple transactions sharing same date:

```python
# EDGE CASE: Check PREVIOUS and NEXT lines for amounts (reverse order)
# Multiple transactions may share same date line in page 5

transactions_found = 0

# Check PREVIOUS line for amounts (transaction before date)
if i > 0 and not rest_of_line:
    prev_line = lines[i - 1].strip()
    numbers_prev_line = re.findall(r'[\d,]+\.[\d]{2}', prev_line)
    
    if len(numbers_prev_line) >= 3:
        # Extract and add transaction
        ...
        transactions_found += 1

# Check NEXT line for amounts (transaction after date)
if i + 1 < len(lines) and not rest_of_line:
    next_line = lines[i + 1].strip()
    numbers_next_line = re.findall(r'[\d,]+\.[\d]{2}', next_line)
    
    if len(numbers_next_line) >= 3:
        # Extract and add transaction
        ...
        transactions_found += 1

# If found transactions in prev/next, skip normal processing
if transactions_found > 0:
    i += 1
    continue
```

**Logic:**
1. Ketika menemukan date line tanpa amounts (`rest_of_line` kosong)
2. Check **PREVIOUS line** untuk pattern debit/credit/balance
3. Check **NEXT line** untuk pattern debit/credit/balance
4. Extract SEMUA transaksi yang valid (bisa 0, 1, atau 2 transaksi)
5. Semua transaksi menggunakan date yang sama

## Hasil Setelah Perbaikan Final

### Ekstraksi
```
✅ Debit: 53 (MATCH dengan PDF summary!)
✅ Credit: 24 (MATCH dengan PDF summary!)
✅ Total: 77 transactions
```

### Transaksi Page 5 Berhasil Di-extract
```
31/03/2026 Credit: 00 Bunga 03101    Rp 159,475.25 ✅
31/03/2026 Debit : Pajak 03101       Rp  31,895.05 ✅
```

### Last 5 Transactions
```
30/03/2026 Debit : OPS Bapak OPS Bapak MCM InhouseTrf KE    Rp 24,000,000.00
31/03/2026 Credit: BRINIDJA/MUHAMMAD RUJALI - 120,850,00    Rp 120,850,000.00
31/03/2026 Debit : Biaya Adm 03101                          Rp     13,000.00
31/03/2026 Credit: 00 Bunga 03101                           Rp    159,475.25 ✅
31/03/2026 Debit : Pajak 03101                              Rp     31,895.05 ✅
```

## File yang Diubah
✅ `backend/processors/mandiri_processor.py` - Handle multiple transactions sharing same date

## Testing
```bash
cd backend
python verify_mandiri_complete.py  # ALL CHECKS PASSED!
```

## Kesimpulan
✅ **Debit: 53** (MATCH!)
✅ **Credit: 24** (MATCH!)
✅ Parser sekarang robust untuk handle:
   - Format normal (date → amounts)
   - Format reverse single (amounts → date)
   - Format reverse multiple (amounts → date → amounts) ← NEW!
✅ Semua edge cases di page 5 berhasil di-handle
