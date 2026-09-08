# 🤖 QUICK START - Telegram Bot MURENA

## ✅ Status: READY TO USE!

Semua fitur IDEB dengan 10 field sudah diimplementasi dan di-test!

---

## 🚀 Cara Menjalankan Bot

### Option 1: Bot Saja (Recommended untuk Production)

```bash
cd backend
python bot_telegram.py
```

### Option 2: Bot + Flask Web (Development)

```bash
cd backend
python run_all.py
```

### Option 3: Windows Batch File

Double-click file:
```
backend/run_bot_only.bat
```

---

## 📱 Cara Menggunakan di Telegram

### 1. Start Bot
```
/start
```
Bot akan menampilkan welcome message dan daftar command.

### 2. Upload IDEB SLIK PDF
```
/ideb
```
Kemudian upload file PDF IDEB SLIK Anda.

### 3. Lihat Hasil
Bot akan menampilkan untuk setiap kredit:

```
━━━━━━━━━━━━━━━━━━━━
*1. PT BPD Kalimantan Selatan*

💰 *Plafon:* 1,250,000,000,00
📈 *Yield:* 3.5%
💵 *O/S:* 982,387,404,00
📅 *Tgl Pencairan:* 12/16/2021
📅 *Tgl Jatuh Tempo:* 12/16/2038
⏱ *Jangka Waktu:* 204 bulan
📊 *Kol:* 1
🏷 *Jenis:* Konsumsi
💳 *Angsuran:* 8,138,755,49
```

### 4. Total Summary
Di akhir, bot menampilkan total:

```
━━━━━━━━━━━━━━━━━━━━
📊 *TOTAL SUMMARY*

💰 *Total Plafon:* Rp 1,457,500,000
💵 *Total O/S:* Rp 1,189,887,404
💳 *Total Angsuran:* Rp 15,057,803
```

### 5. Download Excel
```
/export
```
Pilih format Excel atau CSV.

---

## 🎯 Fitur IDEB yang Ditampilkan

Bot menampilkan **10 field lengkap** untuk setiap kredit:

| No | Field | Source | Notes |
|----|-------|--------|-------|
| 1 | Nama Bank | Pelapor | |
| 2 | Plafon | Plafon Awal | Indonesian format |
| 3 | Yield (%) | Suku Bunga/Imbalan | Persentase |
| 4 | O/S | Baki Debet | Outstanding |
| 5 | Tgl Pencairan | Tanggal Mulai | mm/dd/yyyy |
| 6 | Tgl Jatuh Tempo | Tanggal Jatuh Tempo | mm/dd/yyyy |
| 7 | Jangka Waktu | Calculated | Dalam bulan |
| 8 | Kol | Kualitas | Angka saja (1-5) |
| 9 | Jenis Konsumsi | Jenis Penggunaan | Modal Kerja/Konsumsi/dll |
| 10 | Angsuran | Calculated | PMT formula |

**Plus Total Summary:**
- Total Plafon (SUM)
- Total O/S (SUM)
- Total Angsuran (SUM)

---

## 🔧 Configuration

### Bot Token & User ID

Edit di `bot_telegram.py` (line 36-37):

```python
BOT_TOKEN = "8624088276:AAFPA_9HtGC5hBsD8enfFlNapB7tAYFRDJ8"
AUTHORIZED_USER_ID = 1819390132
```

### Telegram Commands

| Command | Function |
|---------|----------|
| `/start` | Welcome & help |
| `/help` | Show guide |
| `/mutasi` | Upload mutasi rekening (full scan) |
| `/saldo` | Upload untuk saldo harian |
| `/ideb` | Upload IDEB SLIK PDF |
| `/export` | Export hasil (Excel/CSV) |

---

## ✅ Testing

Run test script untuk verify implementasi:

```bash
cd backend
python test_ideb_bot.py
```

Expected output:
```
✅ Bot implementation is READY!

Next steps:
  1. Run bot: python bot_telegram.py
  2. Send /ideb command in Telegram
  3. Upload IDEB PDF file
  4. Verify all 10 fields are displayed
  5. Check Total Summary at the end
```

---

## 📊 Test Files

Sample IDEB files untuk testing:

```
test_data/IDEB PUTRI MAYA.pdf  ✅ (3 credits)
test_data/IDEB RIZKY ADE.pdf   ✅
```

---

## 🐛 Troubleshooting

### Bot tidak start

**Check:**
```bash
# Verify Python dependencies
pip install python-telegram-bot pandas PyMuPDF openpyxl

# Check bot token
echo "BOT_TOKEN ada di bot_telegram.py line 36"

# Test manual
python -c "from bot_telegram import BOT_TOKEN; print(f'Token: {BOT_TOKEN[:10]}...')"
```

### PDF tidak bisa di-parse

**Check:**
```bash
# Test PDF processor
cd backend
python -c "from processors.ideb_processor import process_ideb_file; df = process_ideb_file('../test_data/IDEB PUTRI MAYA.pdf', 'pdf'); print(f'Records: {len(df)}')"
```

Expected: `Records: 3`

### Field tidak muncul

**Verify columns:**
```bash
python -c "from processors.ideb_processor import process_ideb_file; df = process_ideb_file('../test_data/IDEB PUTRI MAYA.pdf', 'pdf'); print(df.columns.tolist())"
```

Expected 10 columns:
```
['Nama Bank', 'Plafon', 'Yield (%)', 'O/S', 'Tanggal Pencairan', 
 'Tanggal Jatuh Tempo', 'Jk Waktu', 'Kol', 'Jenis Konsumsi', 'Angsuran']
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README_BOT.md` | Complete bot documentation |
| `TEST_TELEGRAM_BOT.md` | Implementation details & testing |
| `QUICK_START_BOT.md` | **This file** - Quick start guide |
| `test_ideb_bot.py` | Automated test script |
| `test_bot_config.py` | Configuration test |

---

## 🎉 Ready to Go!

1. ✅ Bot implementation: **COMPLETE**
2. ✅ All 10 IDEB fields: **WORKING**
3. ✅ Total summary: **WORKING**
4. ✅ Excel export: **WORKING**
5. ✅ Tests: **ALL PASS**

**Start your bot now:**

```bash
cd backend
python bot_telegram.py
```

Then open Telegram and send `/ideb` to your bot! 🚀

---

**Last Updated:** September 2, 2026  
**Status:** ✅ Production Ready
