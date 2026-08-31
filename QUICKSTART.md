# 🚀 Quick Start Guide

## Instalasi Pertama Kali

### 1️⃣ Install Dependencies

**Windows:**
```bash
# Double-click file ini:
install.bat
```

**Manual (jika batch file tidak work):**
```bash
# Install Python packages
pip install -r requirements.txt

# Install Node packages
cd frontend
npm install
```

## Menjalankan Aplikasi

### 2️⃣ Start Backend Server

**Windows:**
```bash
# Double-click file ini:
start_backend.bat
```

**Manual:**
```bash
cd backend
python app.py
```

✅ Backend akan jalan di: `http://localhost:5000`

### 3️⃣ Start Frontend Server (Terminal Baru)

**Windows:**
```bash
# Double-click file ini:
start_frontend.bat
```

**Manual:**
```bash
cd frontend
npm start
```

✅ Frontend akan jalan di: `http://localhost:3000`
✅ Browser akan otomatis membuka aplikasi

## Cara Pakai

1. **Pilih Bank**: BSI (CSV) atau Mandiri (PDF)
2. **Upload File**: Klik "📁 Pilih File"
3. **Proses**: Klik "🚀 Upload & Proses"
4. **Lihat Hasil**: Tabel lengkap muncul di web
5. **Copy**: Klik "📋 Copy Semua Data"
6. **Paste**: Buka Excel → Ctrl+V → SELESAI!

**Atau download Excel/CSV jika ingin simpan file**

💡 **Workflow super cepat:** Upload → Copy → Paste (10 detik!)

📖 **Tutorial lengkap:** Baca `CARA_PAKAI_WEB.md`

## Troubleshooting

### Error: "pip not found"
```bash
# Install Python terlebih dahulu dari:
# https://www.python.org/downloads/
```

### Error: "npm not found"
```bash
# Install Node.js terlebih dahulu dari:
# https://nodejs.org/
```

### Error: Port 5000 sudah dipakai
```bash
# Tutup aplikasi yang pakai port 5000, atau ubah di backend/app.py:
# app.run(debug=True, port=5001)  # ganti ke port lain
```

### Error: CORS / Cannot connect to backend
Pastikan:
1. Backend sudah jalan (lihat console, harusnya ada pesan "Running on...")
2. Frontend sudah jalan
3. URL di `frontend/src/App.js` line 5 sesuai: `http://localhost:5000`

### Error: PDF tidak bisa dibaca
- Pastikan PDF asli dari bank (bukan hasil scan)
- PDF harus text-based, bukan image
- Coba export ulang dari aplikasi bank

## File Structure Quick Reference

```
BSI Excel Convert/
├── install.bat              ← Install semua dependencies
├── start_backend.bat        ← Jalankan backend
├── start_frontend.bat       ← Jalankan frontend
├── requirements.txt         ← Python dependencies
├── README.md               ← Full documentation
├── backend/
│   ├── app.py              ← Flask server
│   └── processors/         ← Logic parsing per bank
└── frontend/
    ├── package.json        ← Node dependencies
    └── src/
        ├── App.js          ← Main UI
        └── App.css         ← Styling
```

## Support

Jika ada masalah, cek:
1. Console backend (terminal pertama) untuk error Python
2. Console frontend (terminal kedua) untuk error React
3. Browser DevTools (F12) → Console untuk error JavaScript
4. Browser DevTools → Network untuk melihat API calls

---

**Happy Converting! 🎉**
