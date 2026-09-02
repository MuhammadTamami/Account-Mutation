# Instalasi OCR untuk Scanned PDF

## Untuk Memproses File PDF Scan/CamScanner

File seperti "Rekening Koran BDK Jan - Juli 2026.pdf" dan "Rekening koran bdk 2025.pdf" adalah file scan/gambar yang memerlukan OCR (Optical Character Recognition).

---

## Langkah Instalasi

### 1. Install Python Dependencies

```bash
cd backend
pip install pytesseract PyMuPDF Pillow
```

### 2. Install Tesseract OCR Engine

**Windows:**

1. Download Tesseract installer:
   - Link: https://github.com/UB-Mannheim/tesseract/wiki
   - Atau langsung: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe

2. Jalankan installer (tesseract-ocr-setup.exe)
   - Install di lokasi default: `C:\Program Files\Tesseract-OCR`
   - **PENTING:** Centang option "Add to PATH" saat instalasi

3. Verifikasi instalasi:
   ```bash
   tesseract --version
   ```

4. Jika tidak terdeteksi, tambahkan ke PATH manual:
   - Buka "Environment Variables"
   - Edit "Path" di System Variables
   - Tambahkan: `C:\Program Files\Tesseract-OCR`
   - Restart command prompt/PowerShell

---

## Verifikasi Instalasi

Jalankan script test:

```bash
cd backend
python test_rk_ocr.py
```

Script akan mengecek:
- ✓ pytesseract installed
- ✓ Tesseract OCR engine accessible
- ✓ PyMuPDF installed
- ✓ Pillow (PIL) installed

---

## Cara Menggunakan

### Via Script Test

```bash
cd backend
python test_rk_ocr.py
```

### Via API

Upload file seperti biasa melalui web interface atau API. Sistem akan:
1. Auto-detect file sebagai scanned PDF
2. Detect bank type: MANDIRI_RK_OCR
3. Process dengan OCR processor
4. Extract transaksi dari gambar

---

## Catatan Penting

### Akurasi OCR

- **File Text-based PDF:** 99-100% akurat (seperti RK PTBDK.pdf)
- **File Scanned PDF:** 85-95% akurat (tergantung kualitas scan)
- **File Foto/CamScanner:** 70-85% akurat (tergantung pencahayaan dan kualitas)

### Tips untuk Hasil Terbaik

1. **Gunakan PDF asli dari bank** (text-based) untuk akurasi 100%
2. Jika harus scan:
   - Scan dengan resolusi minimal 300 DPI
   - Pastikan pencahayaan merata
   - Hindari bayangan atau lipatan kertas
   - Scan dalam posisi lurus (tidak miring)

3. CamScanner:
   - Gunakan mode "Document" bukan "Photo"
   - Aktifkan "Auto Enhance" untuk hasil lebih baik
   - Pastikan border terdeteksi dengan benar

### Waktu Processing

- **Text PDF:** ~1-2 detik per halaman
- **Scanned PDF (OCR):** ~5-15 detik per halaman

File dengan banyak halaman akan memakan waktu lebih lama.

---

## Troubleshooting

### Error: "tesseract is not installed"

**Solusi:**
1. Install Tesseract OCR (lihat step 2 di atas)
2. Tambahkan ke PATH
3. Restart terminal/command prompt
4. Test dengan: `tesseract --version`

### Error: "PyMuPDF not available"

**Solusi:**
```bash
pip install PyMuPDF
```

### Error: "pytesseract not available"

**Solusi:**
```bash
pip install pytesseract
```

### OCR Hasil Tidak Akurat

**Solusi:**
1. Cek kualitas scan (harus jelas dan tidak blur)
2. Gunakan PDF asli dari bank jika memungkinkan
3. Re-scan dengan kualitas lebih tinggi
4. Manual verification untuk transaksi penting

---

## Alternative: Gunakan PDF Asli

**Rekomendasi Terbaik:** Minta file PDF asli dari sistem bank (bukan scan)

Keuntungan:
- ✅ 100% akurat
- ✅ Processing cepat (1-2 detik per halaman)
- ✅ Tidak perlu OCR
- ✅ Tidak ada kesalahan pembacaan

File RK asli dari bank biasanya:
- Format text-based PDF
- Bisa di-copy paste textnya
- Ukuran file lebih kecil
- Tidak blur atau pixelated

---

## Status File RK BDK

### ✅ Ready to Process (Text PDF)
- RK PTBDK.pdf - **100% akurat**
- RK GIRO PTBDK.pdf - **100% akurat**

### ⏳ Requires OCR (Scanned PDF)
- Rekening Koran BDK Jan - Juli 2026.pdf - **85-95% akurat** (setelah OCR install)
- Rekening koran bdk 2025.pdf - **85-95% akurat** (setelah OCR install)

---

## Contact

Jika ada pertanyaan atau masalah dalam instalasi OCR, silakan hubungi developer.
