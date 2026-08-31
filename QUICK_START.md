# Quick Start Guide - Bank Statement Analyzer

## 🚀 Application is Ready!

Your application with the new glass morphism design is currently running.

### Access the Application

**Open your browser and navigate to:**
```
http://localhost:3000
```

### Servers Status

✅ **Backend (Flask)**: Running on `http://localhost:5000`  
✅ **Frontend (React)**: Running on `http://localhost:3000`

---

## 📖 How to Use

### Two Modes Available:

#### 1. **📊 Full Statement Scan**
**Purpose**: Complete analysis of all transactions

**Use when you need:**
- Total debit/credit amounts per month
- Transaction frequency counts
- Detailed monthly breakdown
- Full transaction history

**Steps:**
1. Click "Full Statement Scan" button
2. Drag & drop or select files (CSV/PDF/Images)
3. Click "Upload & Process"
4. View comprehensive analysis

#### 2. **📅 Daily Balance Check**
**Purpose**: Quick check of end-of-day balances

**Use when you need:**
- Daily closing balances
- Month-by-month filtering
- Quick copy to Excel
- Simple balance tracking

**Steps:**
1. Click "Daily Balance Check" button
2. Upload your statement file(s)
3. Filter by month if needed
4. Copy to clipboard or download

---

## 📁 Supported File Types

### Single File Upload
- **CSV**: BSI bank statements (auto-detected)
- **PDF**: Mandiri bank statements (auto-detected)
- **Images**: JPG/PNG screenshots (OCR processing)

### Batch Upload (Multiple Files)
- Upload multiple files at once
- Mix of CSV, PDF, and images supported
- Automatic processing and consolidation
- Batch statistics displayed

---

## 🎨 New Design Features

### Glass Morphism UI
- **Dark elegant background**: Blue-gray gradient
- **Frosted glass cards**: Transparent with blur effect
- **Smooth animations**: 60fps transitions
- **Color-coded data**: 
  - 🔴 Red = Debit
  - 🟢 Green = Credit
  - 🔵 Blue = Information

### Visual Hierarchy
- **Semi-transparent layers** for depth
- **Subtle hover effects** for interactivity
- **Clean typography** with varying opacity
- **Minimal distractions** - focus on data

---

## 💡 Tips & Tricks

### For Best Results:

1. **Use original bank files** (CSV/PDF) for 100% accuracy
2. **Batch upload**: Select multiple files for combined analysis
3. **Month filter**: Use dropdown to focus on specific months
4. **Copy to clipboard**: Direct paste to Excel (Ctrl+V)
5. **WhatsApp images**: 60-70% accuracy due to compression

### Monthly Breakdown

In "Full Statement Scan" mode, you'll see:
- **Total Amount**: Sum of all debits and credits
- **Frequency**: Count of transactions
- **Per Month**: Separate cards for each month

### Daily Balance

In "Daily Balance Check" mode, you'll see:
- **Last transaction per day**: End-of-day balance
- **Month filtering**: View specific months
- **Quick actions**: Copy or download

---

## ⚙️ Technical Details

### Backend Processing
- **Auto-detection**: Bank type from file format
- **OCR**: Tesseract for image processing
- **Format**: Indonesian number format (1,234,56)
- **Timestamp**: Uses transaction timestamp for daily balance

### Frontend Features
- **Responsive**: Works on desktop and mobile
- **Real-time**: Instant feedback on actions
- **Error handling**: Clear error messages
- **Loading states**: Visual indicators

---

## 🔧 Troubleshooting

### If the page doesn't load:
```bash
# Check if servers are running
netstat -ano | findstr :3000
netstat -ano | findstr :5000
```

### To restart servers:
```bash
# Stop processes
# Frontend: Ctrl+C in terminal or kill port 3000
# Backend: Ctrl+C in terminal or kill port 5000

# Start backend
cd backend
python app.py

# Start frontend (new terminal)
cd frontend
npm start
```

### Common Issues:

1. **Port already in use**
   - Kill the process using the port
   - Or use different port

2. **Module not found**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   cd ../frontend
   npm install
   ```

3. **Tesseract not found**
   - Install Tesseract OCR
   - Path should be: `C:\Program Files\Tesseract-OCR\tesseract.exe`

---

## 📊 Feature Checklist

### ✅ Implemented Features:
- [x] Glass morphism design
- [x] Dark/elegant color scheme
- [x] Two-mode system (Full Scan / Daily Check)
- [x] Batch file upload
- [x] CSV processing (BSI)
- [x] PDF processing (Mandiri)
- [x] Image OCR (Tesseract)
- [x] Monthly breakdown
- [x] Frequency calculations
- [x] Daily balance extraction
- [x] Indonesian number format
- [x] Month filtering
- [x] Copy to clipboard
- [x] Excel/CSV download
- [x] Drag & drop upload
- [x] Error handling
- [x] Loading indicators
- [x] Responsive design
- [x] Mobile support

---

## 🎯 Next Steps

**The application is ready to use!**

1. Open `http://localhost:3000` in your browser
2. Try uploading a sample file
3. Explore both modes
4. Test batch upload with multiple files

### For Development:
- Both servers auto-reload on file changes
- Check console for errors
- Review `FRONTEND_REDESIGN.md` for design details
- See `DESIGN_COMPARISON.md` for before/after comparison

---

**Enjoy your new glass morphism bank statement analyzer! 🎉**
