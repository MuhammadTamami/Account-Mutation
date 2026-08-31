# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-08-26

### Added
- **Multi-Bank Support**: Added support for 6 banks
  - BSI (Bank Syariah Indonesia) - CSV
  - Mandiri - PDF (4 format variations)
  - BRI - e-Statement BRImo PDF
  - BNI - Transaction Inquiry PDF
  - BCA - Rekening Tahapan PDF
  - Bank Kalsel - Mutasi Rekening PDF
- **Smart Bank Detection**: Auto-detect bank from file content, not filename
- **Password Protected PDF**: Auto-detect and handle Mandiri password-protected PDFs
- **Batch Upload**: Upload up to 100 files simultaneously
- **PyMuPDF Fallback**: Automatic fallback to PyMuPDF when pdfplumber fails
- **Excel Summary Rows**: Download includes Total Mutasi Debit/Kredit/Saldo
- **Custom Number Format**: Format 337,313,654,34 (comma for both thousands and decimal)

### Changed
- **Number Format**: Changed from Indonesian (1.234.567,89) to custom (1,234,567,89)
- **File Organization**: Organized project structure for GitHub
  - test_data/ for PDF/CSV test files
  - tests/ for test scripts
  - docs/development/ for development documentation
- **Max Batch Files**: Increased from 20 to 100 files
- **Max File Size**: Increased from 10MB to 20MB

### Fixed
- **BRI Detection**: Fixed conflict between BRI and Mandiri detection
- **BCA Complex PDF**: Fixed parsing for 71-page BCA PDFs (657+ transactions)
- **Mandiri Password**: Auto-detect password "07031985" for protected PDFs
- **Amount Formatting**: Consistent formatting across all banks
- **Bank Detection Order**: Proper priority to avoid false positives

## [1.3.0] - 2026-08-20

### Added
- **Batch Upload Feature**: Upload multiple files
- **Image OCR Support**: Support JPG/PNG with Tesseract OCR
- **Monthly Filter**: Filter saldo harian by month
- **Badge Indicator**: Show data source (PDF Summary / Calculated)

### Changed
- **UI Redesign**: Modern dark theme with minimalist design
- **Animated Background**: 3D particles and floating documents

### Fixed
- **Timestamp Sorting**: Fixed saldo harian accuracy
- **Negative Debit**: Handle negative debit values correctly
- **CSV Separator**: Auto-detect comma or semicolon

## [1.2.0] - 2026-08-15

### Added
- **PDF Summary Extraction**: Extract totals from Mandiri PDF summary
- **Monthly Breakdown**: Show total amount and frequency per month
- **Copy to Clipboard**: Easy copy-paste workflow

### Fixed
- **Debit Parsing**: Fixed debit transactions not parsing
- **Decimal Format**: Fixed amount 100x too large issue

## [1.1.0] - 2026-08-10

### Added
- **Mandiri PDF Support**: Added Mandiri rekening koran PDF processor
- **Saldo Harian Mode**: Daily balance calculation
- **Download Options**: Excel and CSV formats

### Changed
- **Format Angka**: Indonesian number format (koma as decimal)

## [1.0.0] - 2026-08-05

### Added
- **Initial Release**: BSI CSV to Excel converter
- **Web GUI**: React frontend
- **Flask Backend**: Python processing
- **Basic Features**: Upload, process, download

---

## Legend
- **Added**: New features
- **Changed**: Changes to existing features
- **Fixed**: Bug fixes
- **Removed**: Removed features
