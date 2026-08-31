# Project Structure

## 📁 Folder Organization

```
BSI Excel Convert/
├── .github/              # GitHub configurations
│   └── workflows/        # GitHub Actions (CI/CD)
├── .kiro/                # Kiro IDE configurations (gitignored)
├── .vscode/              # VS Code configurations (gitignored)
├── backend/              # Python Flask backend
│   ├── processors/       # Bank-specific processors
│   │   ├── bsi_processor.py
│   │   ├── mandiri_processor.py
│   │   ├── bri_processor.py
│   │   ├── bni_processor.py
│   │   ├── bca_processor.py
│   │   ├── bank_kalsel_processor.py
│   │   ├── bank_detector.py
│   │   └── image_processor.py
│   ├── uploads/          # Temporary upload folder (gitignored)
│   ├── outputs/          # Generated files (gitignored)
│   └── app.py            # Main Flask application
├── docs/                 # Documentation
│   └── development/      # Development docs (gitignored)
├── frontend/             # React frontend
│   ├── public/
│   ├── src/
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   └── package.json
├── test_data/            # Test PDF/CSV files (gitignored)
├── tests/                # Test scripts (gitignored)
├── whatsapp_pic/         # WhatsApp images (gitignored)
├── .gitattributes        # Git line ending settings
├── .gitignore            # Git ignore rules
├── CHANGELOG.md          # Version history
├── CONTRIBUTING.md       # Contribution guidelines
├── install.bat           # Install dependencies
├── LICENSE               # MIT License
├── QUICK_START.md        # Quick start guide
├── QUICKSTART.md         # Quick start guide (duplicate)
├── README.md             # Main documentation
├── requirements.txt      # Python dependencies
├── start_backend.bat     # Start Flask server
└── start_frontend.bat    # Start React dev server
```

## 🚫 Files Excluded from Git (.gitignore)

### Test & Development Files
- `test_data/` - All PDF, CSV test files
- `tests/` - All test scripts (test_*.py, debug_*.py)
- `docs/development/` - Development documentation
- `whatsapp_pic/` - WhatsApp images

### Generated Files
- `backend/uploads/*` - Temporary uploads
- `backend/outputs/*` - Generated Excel/CSV files
- `frontend/build/` - React build output
- `node_modules/` - Node dependencies
- `__pycache__/` - Python cache

### IDE & System Files
- `.kiro/` - Kiro IDE settings
- `.vscode/` - VS Code settings
- `.idea/` - JetBrains IDEs
- `.DS_Store` - macOS system files

### Sensitive Files
- `.env` - Environment variables
- `*.log` - Log files

## 📄 Important Files (Kept in Git)

### Documentation
- ✅ `README.md` - Main project documentation
- ✅ `CHANGELOG.md` - Version history
- ✅ `QUICK_START.md` - Quick start guide
- ✅ `CONTRIBUTING.md` - Contribution guidelines
- ✅ `LICENSE` - MIT License

### Configuration
- ✅ `.gitignore` - Git ignore rules
- ✅ `.gitattributes` - Line ending settings
- ✅ `requirements.txt` - Python dependencies
- ✅ `frontend/package.json` - Node dependencies

### Scripts
- ✅ `install.bat` - Install all dependencies
- ✅ `start_backend.bat` - Start Flask server
- ✅ `start_frontend.bat` - Start React dev server

### Source Code
- ✅ All `.py` files in `backend/` and `backend/processors/`
- ✅ All `.js`, `.jsx`, `.css` files in `frontend/src/`
- ✅ All `.html` files in `frontend/public/`

## 🔄 Git Workflow

### Before First Push
```bash
cd "c:\Users\muham\Desktop\BSI Excel Convert"
git init
git add .
git commit -m "Initial commit: Multi-bank statement converter v2.0"
git branch -M main
git remote add origin https://github.com/yourusername/bank-statement-converter.git
git push -u origin main
```

### For Updates
```bash
git add .
git commit -m "Your commit message"
git push
```

## 📊 Project Statistics

### Banks Supported
- 6 banks (BSI, Mandiri, BRI, BNI, BCA, Bank Kalsel)

### Processors
- 7 bank processors
- 1 smart bank detector
- 1 image OCR processor

### Features
- Single file upload
- Batch upload (100 files)
- Daily balance mode
- Full transaction mode
- Monthly statistics
- Excel/CSV download
- Copy to clipboard
- Password-protected PDF support
- Dark theme UI

### File Types Supported
- CSV
- PDF
- Excel (XLSX, XLS)
- Images (JPG, PNG)

## 🎯 Ready for GitHub

The project is now organized and ready to push to GitHub:
- ✅ Clean folder structure
- ✅ Comprehensive .gitignore
- ✅ Documentation complete
- ✅ License added
- ✅ Contributing guidelines
- ✅ Line ending settings
- ✅ Test files separated
- ✅ Development docs separated

All test data, development files, and sensitive information are properly excluded from version control.
