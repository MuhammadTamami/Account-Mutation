# Changelog

All notable changes to this project will be documented in this file.

## [2.1.0] - 2026-09-08

### 🎉 Major Update: Balance-Based Detection

#### Added
- **Balance-Based Debit/Credit Detection** for Bank Kalsel, Mandiri, and BSI processors
  - Primary detection now uses balance comparison (current balance vs previous balance)
  - Keyword detection relegated to fallback (first transaction only)
  - **Result**: ALL transactions including monthly fees, admin fees, tax, etc. are now correctly classified as Debit/Kredit

#### Changed
- **Bank Kalsel Processor** (`bank_kalsel_processor.py`)
  - Removed hardcoded special cases (lines 234-246)
  - Removed keyword-based detection (lines 247-265)
  - Implemented balance-based logic: `if balance_diff > 0: Credit, elif balance_diff < 0: Debit`
  
- **Mandiri Processor** (`mandiri_processor.py`)
  - Added balance-based detection for Format 2 (2 numbers: amount + balance only)
  - Previously only handled explicit debit/credit columns
  
- **BSI Processor** (`bsi_processor.py`)
  - Replaced keyword detection in PDF processor with balance-based logic
  - Keywords now only used as fallback for first transaction

#### Fixed
- **100% Accurate Mutation Statistics**
  - Total Mutasi Debet/Kredit now includes ALL transactions without exception
  - Freq Debet/Kredit counts are 100% accurate
  - Monthly fees, admin fees, transaction fees, tax, etc. are all correctly counted

#### Test Results
- ✅ BRI PT HANISA: Monthly Fee ATM (5,000) → Debit
- ✅ BRI HANISA: Minimum Balance Fee (50,000) → Debit
- ✅ Bank Kalsel: All transaction fees, admin fees → Debit
- ✅ Mandiri: Biaya administrasi, biaya transfer, pajak → All Debit
- ✅ Full app flow test: 10/10 files passed

#### Technical Details
```python
# Balance-based detection logic (applied to Bank Kalsel, Mandiri, BSI)
if output_data and len(output_data) > 0:
    prev_balance = float(output_data[-1]['Balance'].replace(',', ''))
    balance_diff = balance - prev_balance
    
    if balance_diff > 0:
        transaction_type = 'Credit'  # Balance increased
    elif balance_diff < 0:
        transaction_type = 'Debit'   # Balance decreased
else:
    # Fallback: Enhanced keyword detection (first transaction only)
```

#### User Impact
- **Problem**: User reported that monthly fees and other charges were not included in mutation statistics because they relied on keyword detection
- **Solution**: Switched to balance-based detection which captures ALL transactions regardless of description keywords
- **User Requirement**: "jangan ambil dari keterangan, tapi dari debet dan kredit aja" ✅ Fulfilled

---

## [2.0.0] - 2026-08-24

### Added
- **IDEB SLIK Analyzer**
  - Analyze credit/loan data from IDEB SLIK PDF
  - Filter by Baki Debet > 0
  - Export to CSV/Excel with totals

- **Multi-Bank Support**
  - BSI (CSV, PDF, Excel)
  - Mandiri (PDF with password support)
  - BCA (PDF)
  - BRI (PDF with balance-based detection)
  - BNI (PDF)
  - Bank Kalsel (PDF)
  - Auto-detection for bank type

- **Multi-Format Support**
  - CSV files
  - PDF files (with OCR)
  - Excel files (.xlsx, .xls)
  - Image files (.jpg, .png) with OCR

- **Batch Upload**
  - Upload up to 100 files simultaneously
  - Max 20MB per file

- **Password-Protected PDF**
  - Support for Mandiri e-Statement with password

- **Smart Filter & Download**
  - Filter by month
  - Filter by date range
  - Download respects active filters

- **Real-time Statistics**
  - Total Mutasi Debet/Kredit
  - Freq Debet/Kredit
  - Updates dynamically with filters

### Changed
- Complete UI redesign with 3D animated background
- Improved navigation and user experience
- Better error handling and user feedback

### Fixed
- BRI processor header skip logic (prevent skipping "Minimum Balance Fee")
- BRI teller ID detection (check if last word looks like teller ID)
- Daily balance format (YYYY-MM-DD)
- Mutation statistics calculation

---

## [1.0.0] - 2026-06-01

### Initial Release
- Basic bank statement processing
- CSV to Excel conversion
- Simple UI
- Single file upload
