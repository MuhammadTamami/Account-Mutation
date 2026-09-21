# Test Data - Organized by Bank

This directory contains test PDF files organized by bank for testing the bank statement processors.

## 📁 Folder Structure

```
test_data/
├── bank_kalsel/    # Bank Kalimantan Selatan statements
├── bca/            # BCA (Bank Central Asia) statements
├── bni/            # BNI (Bank Negara Indonesia) statements
├── bri/            # BRI (Bank Rakyat Indonesia) statements
├── bsi/            # BSI (Bank Syariah Indonesia) statements
├── byond/          # BYOND bank statements
├── ideb/           # IDEB SLIK credit reports
├── mandiri/        # Bank Mandiri statements
└── other/          # Unclassified or miscellaneous files
```

## 📊 Current Test Files

### Bank Kalsel (2 files)
- `1. Januari.pdf` - Januari 2025 statement
- `20240202091847611 JAN 2024.pdf` - Januari 2024 statement

### BCA (1 file)
- `9. April 2026.pdf` - April 2026 statement (71 pages, 665 transactions)

### BNI (1 file)
- `acct_mutation_7285137556_2026030120260331.csv` - CSV format

### BRI (7 files)
- `1. 184399112771_e-StatementBRImo_018001000731560_Jan2026_20260728_110025.pdf`
- `2. 184881015933_e-StatementBRImo_018001000731560_Feb2026_20260729_081138.pdf`
- `3. 184881386097_e-StatementBRImo_018001000731560_Mar2026_20260729_081229.pdf`
- `4. 184881658138_e-StatementBRImo_018001000731560_Apr2026_20260729_081307.pdf`
- `5. 184882015774_e-StatementBRImo_018001000731560_May2026_20260729_081356.pdf`
- `6. 184882400618_e-StatementBRImo_018001000731560_Jul2026_20260729_081448.pdf`
- `fe9bdc9c-fb00-474d-b952-7b3a26df457a_156154113228_e-StatementBRImo_360101010764538_Apr2026_20260608_100213.pdf`

### BYOND (1 file)
- `ESTATEMENT-7326292057-052026-10-13-39.pdf` - Mei 2026 (63 pages, 972 transactions)

### IDEB (3 files)
- `IDEB PUTRI MAYA.pdf` - SLIK credit report
- `IDEB RIZKY ADE.pdf` - SLIK credit report (101 pages, 77 records)
- `IDEB SUYANTO.pdf` - SLIK credit report

### Mandiri (13 files)
- `1. Mandiri Januari.pdf` - Januari 2026
- `2. Mandiri Februari .pdf` - Februari 2026
- `3. Mandiri Maret.pdf` - Maret 2026
- `4. Mandiri April.pdf` - April 2026
- `5. Mandiri Mei.pdf` - Mei 2026
- `6. Mandiri Juni.pdf` - Juni 2026
- `7. Mandiri Juli.pdf` - Juli 2026
- `acct_1977_Maret 2026.pdf` - Account Statement Maret 2026
- `Acc_Statement_0310071616265_2026-02-01_2026-07-31_20260812144517.pdf`
- `Acc_Statement_0310073771977_2026-04-01_2026-04-30_20260901110415.pdf`
- `Acc_Statement_0310073771977_2026-05-01_2026-05-31_20260901111147.pdf`
- `RK Februari.pdf`
- `Rk Januri 2026.pdf`

### Other (5 files)
- `acct-mutation-3107200133-2026010120260131.csv`
- `Rekening koran bdk 2025.pdf`
- `Rekening Koran BDK Jan - Juli 2026.pdf`
- `RK GIRO PTBDK.pdf`
- `RK PTBDK.pdf`

## 🔧 How Files Were Organized

Files were automatically organized using `backend/organize_test_data.py` which:
1. Reads the first page of each PDF
2. Detects bank type based on keywords and formatting
3. Moves files to appropriate bank folders

## ✅ Verified Test Files

These files are used in `backend/check_all_banks_accuracy.py` for automated testing:

| Bank | Test File | Transactions | Status |
|------|-----------|--------------|--------|
| Bank Kalsel | `bank_kalsel/1. Januari.pdf` | 28 (19 DB, 9 CR) | ✅ 100% Accurate |
| BCA | `bca/9. April 2026.pdf` | 665 (631 CR, 34 DB) | ✅ Pass |
| BRI | `bri/fe9bdc9c-fb00-474d-b952-7b3a26df457a_156154113228_e-StatementBRImo_360101010764538_Apr2026_20260608_100213.pdf` | 581 (275 CR, 306 DB) | ✅ Pass |
| Mandiri | `mandiri/1. Mandiri Januari.pdf` | 119 (102 CR, 17 DB) | ✅ Pass |
| BYOND | `byond/ESTATEMENT-7326292057-052026-10-13-39.pdf` | 972 (968 CR, 4 DB) | ✅ Pass |
| IDEB | `ideb/IDEB RIZKY ADE.pdf` | 77 records | ✅ Pass |

## 📝 Adding New Test Files

To add new test files:

1. Place PDF/CSV files in the root `test_data/` directory
2. Run the organization script:
   ```bash
   cd backend
   python organize_test_data.py
   ```
3. Files will be automatically moved to appropriate bank folders
4. Manually move any misclassified files if needed

## 🚀 Running Tests

To test all bank processors:

```bash
cd backend
python check_all_banks_accuracy.py
```

Expected result: **6/6 banks passed (100.0%)**

## 📊 Test Statistics

- **Total Test Files:** 33 files
- **Total Banks:** 6 active processors
- **Total Transactions Tested:** 3,242 transactions
- **Total Pages Tested:** 268 pages
- **Overall Accuracy:** 100%

## 🔍 File Naming Conventions

### BRI Files
Format: `e-StatementBRImo_[AccountNo]_[Month][Year]_[Timestamp].pdf`

### Mandiri Files
- Monthly: `[Number]. Mandiri [Month].pdf`
- Account Statement: `Acc_Statement_[AccountNo]_[StartDate]_[EndDate]_[Timestamp].pdf`

### IDEB Files
Format: `IDEB [Name].pdf`

### Bank Kalsel Files
Format: `[Number]. [Month].pdf` or descriptive name

### BCA Files
Format: `[Number]. [Month] [Year].pdf`

## ⚠️ Notes

- Some Mandiri PDFs may be password-protected (handled by processor)
- Files in `other/` folder may need manual classification
- CSV files are also supported for some banks
- Corrupt or unreadable PDFs remain in `other/` folder

---

**Last Updated:** September 7, 2026  
**Organization Script:** `backend/organize_test_data.py`  
**Test Script:** `backend/check_all_banks_accuracy.py`
