# 🚀 Quick Start - Generate All Diagrams

## ⚡ Fastest Way (1 Command)

### Windows:
```bash
cd docs/images
generate-all.bat
```

### PowerShell (Recommended):
```powershell
cd docs/images
.\generate-all.ps1
```

### Want SVG instead of PNG?
```powershell
cd docs/images
.\generate-all-svg.ps1
```

---

## ✅ What You'll Get

After running the script, you'll have **7 PNG images**:

1. ✅ `version-timeline.png` - Development timeline
2. ✅ `bank-accuracy-chart.png` - Accuracy comparison
3. ✅ `architecture-diagram.png` - System architecture
4. ✅ `feature-comparison.png` - Version evolution
5. ✅ `processing-modes.png` - 4 modes flowchart
6. ✅ `statistics-dashboard.png` - Stats overview
7. ✅ `user-workflow.png` - User journey

---

## 📝 Next Steps

### 1. Verify Images Generated
```bash
# Check if all images exist
dir *.png
```

### 2. Add to Main README.md
Copy this to your main README.md:

```markdown
## 📊 Visual Overview

### Processing Modes
![Processing Modes](docs/images/processing-modes.png)

*4 specialized processing modes: Full Scan, Daily Balance, IDEB SLIK, and Angsuran KOP*

### Bank Support & Accuracy
![Bank Accuracy](docs/images/bank-accuracy-chart.png)

*Support for 7+ banks with 95-100% accuracy rates*

### System Architecture
![Architecture](docs/images/architecture-diagram.png)

*Modern architecture with Web + Bot Telegram access*
```

### 3. Commit to Git
```bash
git add docs/images/*.png
git commit -m "docs: Add visual diagrams for documentation"
git push
```

---

## 🔧 Troubleshooting

### Error: "mmdc is not recognized"
**Solution**: Install Mermaid CLI first
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Error: "Cannot find module 'puppeteer'"
**Solution**: Reinstall with puppeteer
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Error: Chromium download fails
**Solution**: Use alternative renderer
```bash
# Use puppeteer manually
npm install -g puppeteer
```

### Script doesn't run in PowerShell
**Solution**: Enable script execution
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## 🎨 Alternative: Use Mermaid Live

If CLI doesn't work, use the web version:

1. Go to **https://mermaid.live**
2. Open any `.mmd` file in this folder
3. Copy the content
4. Paste in Mermaid Live
5. Click "Actions" → "PNG"
6. Download and save here

**Repeat for all 7 files.**

---

## 📊 Expected Output

```
docs/images/
├── version-timeline.png          ✅ Generated
├── bank-accuracy-chart.png       ✅ Generated
├── architecture-diagram.png      ✅ Generated
├── feature-comparison.png        ✅ Generated
├── processing-modes.png          ✅ Generated
├── statistics-dashboard.png      ✅ Generated
└── user-workflow.png             ✅ Generated
```

**Total: 7 PNG files ready for documentation!**

---

## 💡 Tips

1. **PNG vs SVG**:
   - Use PNG for web/docs (smaller file size)
   - Use SVG for printing (scalable, no quality loss)

2. **Transparent Background**:
   - PNG files have transparent background
   - Works on any background color

3. **File Size**:
   - Each PNG: ~50-200KB
   - SVG files are usually smaller

4. **Regenerate Anytime**:
   - Just run the script again
   - Safe to overwrite

---

## ✅ Done?

After generating, your visual documentation is ready!

Check [README.md](README.md) for AI generation prompts if you want custom graphics instead.
