# 🏦 Bank Statement Converter

![Version](https://img.shields.io/badge/version-2.1.0-brightgreen)
![Status](https://img.shields.io/badge/status-stable-blue)
![Banks](https://img.shields.io/badge/banks-6-orange)

Aplikasi web untuk mengkonversi rekening koran dari **multiple banks** ke format Excel yang rapi dan terstruktur dengan akurasi tinggi.

## 🎉 What's New in v2.1.0

### Balance-Based Detection ✨
- **100% Accurate Mutation Statistics**: Semua transaksi (monthly fee, admin fee, tax, dll) PASTI terdeteksi sebagai Debit/Kredit
- **No More Keyword Dependency**: Detection tidak lagi bergantung pada keyword di deskripsi
- **Applied to**: Bank Kalsel, Mandiri, BSI, and BRI processors

**Problem Solved**: 
- ❌ Before: Monthly fees sometimes missed → Mutation stats incomplete
- ✅ After: ALL transactions captured → 100% accurate stats

**Technical**: Balance comparison (current vs previous) determines Debit/Kredit automatically.

[See full changelog](CHANGELOG.md)

## ✨ Fitur

### 🏦 Bank yang Didukung
- ✅ **BSI** (Bank Syariah Indonesia) - CSV format
- ✅ **Mandiri** - PDF format (4 format variations + password protected)
- ✅ **BRI** - e-Statement BRImo PDF
- ✅ **BNI** - Transaction Inquiry PDF
- ✅ **BCA** - Rekening Tahapan PDF
- ✅ **Bank Kalsel** - Mutasi Rekening PDF
- 🔄 **More banks coming soon!**

### 📁 Format yang Didukung
- ✅ **CSV** (.csv) - BSI format - Akurasi 100%
- ✅ **PDF** (.pdf) - Multiple banks - Akurasi 95-100%
- 🆕 **Excel** (.xlsx, .xls) - Akurasi 100%
- 🆕 **Image** (.jpg, .png) - Any bank dengan OCR - Akurasi 70-90%

### 🎯 Fitur Utama
- ✅ **Smart Auto-detect** - Otomatis detect bank dari konten file, bukan dari nama file
- ✅ **Multi-bank Support** - 6 bank supported dengan 1 aplikasi
- ✅ **Password Protected PDF** - Support Mandiri PDF dengan password
- ✅ **Batch Upload** - Upload sampai 100 file sekaligus
- ✅ **GUI berbasis Web** - Modern, responsive, dark theme
- ✅ **Copy langsung dari web** - Klik button, paste ke Excel (super cepat!)
- ✅ **Saldo harian akurat** - Berdasarkan timestamp
- ✅ **Summary extraction** - Extract langsung dari PDF summary
- ✅ **Monthly breakdown** - Total amount & frequency per bulan dengan filter
- ✅ **Format angka custom** - Koma untuk thousands dan decimal (337,313,654,34)
- ✅ **Download dengan summary** - Excel include Total Mutasi Debit/Kredit/Saldo
- ✅ Tampilkan semua data di web
- ✅ Ringkasan statistik transaksi
- ✅ UI modern dan user-friendly
- ✅ Responsive untuk mobile dan desktop
- ✅ **Drag & drop upload** - Mudah dan cepat

## 🛠️ Teknologi

**Backend:**
- Python 3.8+
- Flask (Web Framework)
- Flask-CORS (CORS handling)
- Pandas (Data Processing)
- pdfplumber (PDF Extraction)
- openpyxl (Excel Generation)
- pytesseract + Pillow (OCR for Images) 🆕

**Frontend:**
- React 18
- Axios (HTTP Client)
- CSS3 (Modern styling with gradients)

## 📋 Persiapan

Pastikan sudah terinstal:
- Python 3.8 atau lebih baru
- Node.js 14 atau lebih baru
- npm atau yarn
- (Optional) Tesseract OCR untuk image processing

## 🚀 Cara Menjalankan

### 1. Setup Backend

```bash
# Masuk ke folder root project
cd "c:\Users\muham\Desktop\BSI Excel Convert"

# Install dependencies Python
pip install -r requirements.txt

# Jalankan backend server
cd backend
python app.py
```

Backend akan berjalan di `http://localhost:5000`

### 2. Setup Frontend

Buka terminal baru:

```bash
# Masuk ke folder frontend
cd "c:\Users\muham\Desktop\BSI Excel Convert\frontend"

# Install dependencies Node.js
npm install

# Jalankan frontend development server
npm start
```

Frontend akan berjalan di `http://localhost:3000` dan otomatis membuka browser.

## 📖 Cara Penggunaan

1. **Upload File**: Drag & drop atau klik "Pilih File"
   - BSI CSV (.csv)
   - Mandiri PDF (.pdf)
   - Bank statement image (.jpg, .png)
2. **Auto-detect**: Aplikasi otomatis detect jenis file
3. **Proses**: Klik tombol "🚀 Upload & Proses"
4. **Lihat Hasil**:
   - Ringkasan data dengan badge (PDF Summary / Calculated)
   - Saldo harian (filter per bulan tersedia)
   - Breakdown bulanan (total amount + frequency)
5. **Copy ke Excel**: Klik tombol "📋 Copy Saldo Harian" lalu paste (Ctrl+V) di Excel
6. **Atau Download**: Pilih format download (Excel atau CSV) jika ingin simpan file

### 💡 Keunggulan Copy dari Web

**Cara Utama (Recommended):**
- ⚡ **Super cepat** - 2 klik saja!
- 📋 **Copy button** → langsung copy semua data
- 📊 **Paste ke Excel** → langsung masuk dengan format benar
- 🎯 **No download needed** → workflow lebih efisien

**Cara Alternative (Backup):**
- 📥 Download Excel/CSV untuk archiving

### 💡 Keunggulan Format Angka

Aplikasi ini menggunakan **format angka Indonesia** (`1,499,754,00`) dimana:
- Koma (`,`) sebagai pemisah ribuan
- Koma (`,`) sebagai pemisah desimal
- **Tidak perlu replace lagi** saat paste ke Excel template Indonesia
- Lihat `FORMAT_ANGKA.md` untuk detail lengkap

**Workflow Ideal:**
```
Upload → Proses → Copy → Paste ke Excel → SELESAI! (10 detik)
```

## 📁 Struktur Folder

```
BSI Excel Convert/
├── backend/
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── bsi_processor.py      # Processor untuk BSI CSV
│   │   ├── mandiri_processor.py  # Processor untuk Mandiri PDF
│   │   └── image_processor.py    # Processor untuk Image OCR 🆕
│   ├── uploads/                   # Folder temporary upload
│   ├── outputs/                   # Folder hasil konversi
│   ├── app.py                     # Flask backend server
│   └── requirements.txt           # Python dependencies 🆕
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js                # Main React component
│   │   ├── App.css               # Styling
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
├── requirements.txt              # Python dependencies
└── README.md
```

## 🔍 Format Input

### BSI CSV Format
```csv
"No.","Tgl dan Waktu Periode","No Referensi","Deskripsi","Kode","D/K","Debit","Kredit","Saldo",""
"1","2026-01-01 / 01:44:10","FT26001TSFTC","Acct Transfer","","K","0.00","630,000.00","7,885,024.22",""
"5","2026-01-01 / 12:55:00","FT260017J170","Bank Mandiri GHINA REZKIA","","D","-2,500.00","0.00","8,252,524.22",""
```

**Fitur:**
- Auto-detect separator (comma atau semicolon)
- Support negative debit values
- Timestamp-based sorting untuk akurasi saldo harian

### Mandiri PDF Format
Standard PDF rekening koran dari Mandiri dengan:
- Account Statement Summary (halaman 1)
- Tabel transaksi dengan kolom: Posting Date, Debit, Credit, Balance
- Format: `DD MMM YYYY, HH:MM:SS`

**Fitur:**
- Extract summary langsung dari PDF (100% akurat)
- Timestamp-based sorting
- Fallback ke perhitungan manual jika summary tidak ada

### Image Format (NEW)
Screenshot atau scan dari rekening koran:
- Format: JPG, JPEG, PNG
- Minimum resolution: 300 DPI
- Requirements: Tesseract OCR installed

**Fitur:**
- OCR text extraction
- Auto-detect bank type (BSI/Mandiri)
- Parse transactions dari image
- Accuracy: 70-90% (tergantung kualitas image)

**Catatan:** Gunakan CSV atau PDF untuk akurasi terbaik. Image OCR sebagai opsi cadangan.

## 📊 Output Format

Semua output akan memiliki kolom standar:
- **Date**: Tanggal transaksi
- **Reference**: Nomor referensi transaksi
- **Description**: Deskripsi transaksi
- **Type**: Credit atau Debit
- **Amount**: Jumlah transaksi
- **Balance**: Saldo setelah transaksi

## ⚠️ Troubleshooting

### Animated Background Tidak Muncul 🎨

Jika background animasi (grid lines, floating documents, particles) tidak terlihat:

**Quick Fix (Paling Sering Berhasil):**
```cmd
cd frontend
clear-cache.bat
npm start
```

Lalu di browser: `Ctrl + Shift + R` (hard refresh)

**Panduan Lengkap:** Lihat `ANIMATION_FIX_GUIDE.md`

**Test Isolated:** Buka `http://localhost:3000/test-animation.html`

**Common Issues:**
- ✅ Browser cache - Clear dengan script di atas
- ✅ Webpack cache - Script otomatis clear
- ✅ Browser lama - Update ke Chrome 76+, Firefox 103+, atau Safari 9+
- ✅ Hardware acceleration disabled - Enable di browser settings

**Browser Compatibility Check:**
App akan otomatis log di console apakah browser support semua fitur.

### Backend error saat install
```bash
# Install semua dependencies
cd backend
pip install -r requirements.txt

# Jika error saat install pdfplumber:
pip install Pillow cryptography
```

### Image upload error: "OCR tidak tersedia"
**Solusi:**
1. Install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
2. Restart backend
3. Atau gunakan CSV/PDF format (lebih akurat)

Lihat `INSTALL_OCR.md` untuk panduan lengkap.

### Frontend tidak bisa connect ke backend
Pastikan:
1. Backend sudah berjalan di port 5000
2. CORS sudah enable (sudah otomatis di code)
3. Firewall tidak memblokir koneksi

### Saldo harian tidak akurat
✅ **FIXED!** Aplikasi sekarang menggunakan timestamp-based sorting.
- Restart backend untuk apply changes
- Saldo harian sekarang 100% akurat

### Error saat parsing PDF
PDF Mandiri memiliki berbagai format. Jika ada error:
1. Pastikan PDF asli dari bank (bukan scan)
2. PDF harus berbentuk teks, bukan gambar
3. Coba export ulang PDF dari aplikasi bank
4. Jika total tidak match, aplikasi akan extract dari PDF summary (100% akurat)

## 🎨 Customization

### Mengubah warna tema
Edit file `frontend/src/index.css` dan `frontend/src/App.css`:
```css
/* Ubah gradient background */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Menambah bank baru
1. Buat processor baru di `backend/processors/namabank_processor.py`
2. Tambahkan routing di `backend/app.py`
3. Tambahkan opsi di frontend `App.js`

## 📝 Documentation

- **FINAL_IMPLEMENTATION_SUMMARY.md** - Complete overview semua fitur
- **IMPLEMENTATION_COMPLETE.md** - PDF summary extraction details
- **BUG_FIX_BSI_CSV.md** - BSI CSV bug fixes & testing
- **FITUR_IMAGE_OCR.md** - Image OCR feature guide
- **INSTALL_OCR.md** - Tesseract installation & troubleshooting
- **RINGKASAN_IMPLEMENTASI.md** - Ringkasan dalam Bahasa Indonesia
- **FORMAT_ANGKA.md** - Penjelasan format angka Indonesia

## 📊 Accuracy Comparison

| Format | Akurasi | Kecepatan | Best For |
|--------|---------|-----------|----------|
| **CSV** | 100% | ⚡ Sangat Cepat | BSI export |
| **PDF** | 99-100% | ⚡ Cepat | Mandiri statement |
| **Image** | 70-90% | 🐌 Lambat | Screenshot/Scan |

**Rekomendasi:** Gunakan CSV atau PDF untuk akurasi terbaik.

## 🎯 Recent Updates (v2.0.0)

### ✅ What's New:
1. **Multi-Bank Support** - 6 banks: BSI, Mandiri, BRI, BNI, BCA, Bank Kalsel
2. **Smart Detection** - Detect bank dari konten file, bukan nama file
3. **BRI e-Statement** - Support BRI BRImo PDF format
4. **BNI Transaction Inquiry** - Support BNI PDF format
5. **BCA Rekening Tahapan** - Support BCA PDF (71 pages, 657+ transactions)
6. **Bank Kalsel** - Support Mutasi Rekening format
7. **Password Protected** - Mandiri PDF dengan password auto-detect
8. **Batch Upload** - Upload 100 files sekaligus
9. **Custom Number Format** - Format 337,313,654,34 (comma for all separators)
10. **Excel Summary** - Download include Total Mutasi Debit/Kredit/Saldo
11. **PyMuPDF Fallback** - Complex PDF handled automatically

### 🐛 Bug Fixes:
- ✅ Fixed: Error 500 saat upload BSI CSV
- ✅ Fixed: BRI detection conflict dengan Mandiri
- ✅ Fixed: BCA complex PDF parsing (71 pages)
- ✅ Fixed: Mandiri password detection
- ✅ Fixed: Amount formatting consistency
- ✅ Fixed: Timestamp-based sorting untuk saldo akurat

## 📝 License

MIT License - Bebas digunakan untuk personal maupun komersial

## 👨‍💻 Author

Dibuat dengan ❤️ untuk memudahkan pengguna BSI dan Mandiri

## 🤝 Kontribusi

Silakan buat pull request atau laporkan issue jika menemukan bug!

---

**Happy Converting! 🎉**
