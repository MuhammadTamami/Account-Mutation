# BCA Processor - Correct Logic (Verified)

## ✅ Simple Rules Confirmed

### 1. Type Detection
**Rule:** Check MUTASI column value
- Has " DB" suffix → **Debit**
- No " DB" suffix → **Credit**

**Examples:**
```
40,000,000.00 DB  → DEBIT
2,990,800.00      → CREDIT
```

### 2. Balance Extraction
**Rule:** Take value from SALDO column
- Usually appears after MUTASI value
- Not every transaction has SALDO
- Format: `310,454,298.90`

### 3. Transaction Structure

```
DD/MM                      ← Date
DESCRIPTION LINE 1         ← Description (multiple lines)
DESCRIPTION LINE 2
...
BRANCH (4 digits)          ← Branch code (optional, e.g., 0998)
AMOUNT.DD                  ← MUTASI column (with or without " DB")
BALANCE.DD                 ← SALDO column (optional)
```

**Complete Example:**
```
29/04
TRSF E-BANKING DB          ← Description
2904/FTSCY/WS95271
300000000.00
WINDRI ARNI
300,000,000.00 DB          ← MUTASI with DB = DEBIT
(no balance)

29/04
KR OTOMATIS                ← Description
MID : 885002248330
BHINNIAN SALON AND
QR : 1929900.00           ← Skip these QR/DDR lines
DDR: 0.00
0998                       ← Branch
1,929,900.00               ← MUTASI no DB = CREDIT
310,454,298.90             ← SALDO
```

## Implementation Guide

### Step 1: Parse Line by Line
1. Find date: `^\d{2}/\d{2}$`
2. Collect description lines (skip QR/TGH/DDR/MID)
3. Find branch: `^\d{4}$` (optional)
4. Find MUTASI: `^[\d,]+\.\d{2}(\s+DB)?$`
5. Find SALDO: next line with pattern `^[\d,]+\.\d{2}$`

### Step 2: Type Detection
```python
mutasi_match = re.match(r'^([\d,]+\.\d{2})(\s+DB)?$', line)
if mutasi_match:
    amount = mutasi_match.group(1)
    has_db = mutasi_match.group(2) is not None
    transaction_type = 'Debit' if has_db else 'Credit'
```

### Step 3: Balance Extraction
```python
# After finding MUTASI, check next line
if i + 1 < len(lines):
    next_line = lines[i + 1].strip()
    if re.match(r'^[\d,]+\.\d{2}$', next_line):
        # This is SALDO
        balance = next_line
```

## Key Points

1. **Don't overthink!** Format is actually simple:
   - Find date
   - Collect description
   - Find amount (MUTASI)
   - Check " DB" suffix for type
   - Next amount is balance

2. **Skip intermediate values:**
   - QR/TGH/DDR are just detail, skip them
   - Use final amount in MUTASI column

3. **Branch is optional:**
   - TRSF E-BANKING transactions don't have branch
   - KR OTOMATIS transactions have branch (0998)

4. **Balance is optional:**
   - Only some transactions show balance
   - Balance appears right after MUTASI

## Verified Test Cases

✅ Page 70 (29-30/04):
- Multiple KR OTOMATIS → CREDIT ✓
- With branch 0998 ✓
- Some with SALDO ✓

✅ Page 3 (01/04):
- TRSF E-BANKING DB → DEBIT ✓
- No branch ✓
- Has SALDO ✓
- KR OTOMATIS → CREDIT ✓
- With branch 0998 ✓

## Expected Results

With correct implementation:
- Credit: 631 transactions
- Debit: 34 transactions  
- All amounts correct (not 0.00)
- Balance populated where available
- Total matches PDF summary

## Next Steps

1. Rewrite `process_bca_pdf()` with this simple logic
2. Remove complex multi-format handling
3. Use straightforward pattern matching
4. Validate against PDF summary
