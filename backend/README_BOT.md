# 🤖 MURENA Telegram Bot

Telegram Bot untuk analisis mutasi rekening yang terintegrasi dengan aplikasi MURENA.

## 📋 Fitur

✅ Upload dan analisis mutasi rekening via Telegram
✅ Support semua bank: BSI, Mandiri, BCA, BRI, BNI, Bank Kalsel, Byond
✅ IDEB SLIK analyzer
✅ Export hasil ke Excel/CSV
✅ Mode Full Scan dan Daily Balance

## 🔧 Instalasi

### 1. Install Dependencies

```bash
pip install -r requirements_bot.txt
```

### 2. Konfigurasi (Opsional)

Bot sudah dikonfigurasi dengan:
- Token: `8624088276:AAFPA_9HtGC5hBsD8enfFlNapB7tAYFRDJ8`
- Authorized User: `1819390132`

Jika ingin mengubah, edit file `bot_telegram.py`:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN"
AUTHORIZED_USER_ID = YOUR_USER_ID
```

## 🚀 Cara Menjalankan

### Opsi 1: Bot Saja

```bash
python bot_telegram.py
```

Atau double-click: `run_bot_only.bat`

### Opsi 2: Bot + Flask App Bersamaan

```bash
python run_all.py
```

### Opsi 3: Manual (2 Terminal)

**Terminal 1 - Flask App:**
```bash
python app.py
```

**Terminal 2 - Telegram Bot:**
```bash
python bot_telegram.py
```

## 📱 Penggunaan

### 1. Start Bot
Buka Telegram, cari bot Anda, lalu:
```
/start
```

### 2. Commands Available

| Command | Deskripsi |
|---------|-----------|
| `/start` | Mulai bot dan lihat welcome message |
| `/help` | Panduan lengkap |
| `/mutasi` | Upload untuk full scan mutasi |
| `/saldo` | Upload untuk cek saldo harian |
| `/ideb` | Upload IDEB SLIK PDF |
| `/export` | Export hasil terakhir (Excel/CSV) |

### 3. Workflow

**Full Scan Mutasi:**
1. Ketik `/mutasi`
2. Kirim file PDF/CSV/Excel/Image
3. Bot akan menganalisis dan kirim ringkasan
4. Gunakan `/export` untuk download file Excel/CSV

**Saldo Harian:**
1. Ketik `/saldo`
2. Kirim file mutasi
3. Bot akan extract saldo penutupan per hari
4. Gunakan `/export` untuk download

**IDEB SLIK:**
1. Ketik `/ideb`
2. Kirim PDF IDEB SLIK
3. Bot akan extract kredit dengan Baki Debet > 0
4. Gunakan `/export` untuk download

## 🔒 Keamanan

- ✅ Hanya User ID `1819390132` yang bisa akses bot
- ✅ File otomatis dihapus setelah diproses
- ✅ Session per user (isolated)
- ✅ No data stored permanently

## 📁 Struktur File

```
backend/
├── bot_telegram.py          # Main bot file
├── run_all.py              # Run bot + Flask bersamaan
├── run_bot_only.bat        # Run bot saja (Windows)
├── requirements_bot.txt    # Bot dependencies
├── bot_temp/              # Temporary folder untuk uploaded files
└── outputs/               # Output folder untuk export files
```

## 🐛 Troubleshooting

### Bot tidak respond
- Pastikan token benar
- Check koneksi internet
- Lihat log error di terminal

### "You don't have access"
- Pastikan User ID Anda `1819390132`
- Atau update `AUTHORIZED_USER_ID` di bot_telegram.py

### Error "Module not found"
```bash
pip install -r requirements_bot.txt
```

### File terlalu besar
- Maksimal file size: 20MB
- Telegram limit: 50MB
- Kompres file jika perlu

## 📝 Logs

Bot akan print log di terminal:
- ✅ File received
- 🔍 Bank detected
- ⏳ Processing...
- ✅ Done

## 🎯 Next Steps

Setelah bot berjalan:
1. Test dengan `/start`
2. Upload file test dengan `/mutasi`
3. Check hasil dengan `/export`
4. Gunakan untuk file production

## ⚙️ Advanced Configuration

### Menambah User Authorized

Edit `bot_telegram.py`:
```python
AUTHORIZED_USERS = [1819390132, 123456789, 987654321]

def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_USERS
```

### Custom Export Format

Modifikasi fungsi `export_to_excel()` dan `export_to_csv()` di `bot_telegram.py`.

### Webhook (Production)

Untuk production, gunakan webhook instead of polling:
```python
application.run_webhook(
    listen="0.0.0.0",
    port=8443,
    url_path="YOUR_TOKEN",
    webhook_url="https://yourdomain.com/YOUR_TOKEN"
)
```

## 📞 Support

Jika ada masalah, check:
1. Log di terminal
2. Telegram Bot API status
3. Internet connection
4. File format compatibility

---

**Built with ❤️ using python-telegram-bot**
