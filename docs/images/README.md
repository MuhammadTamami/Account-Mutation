# 📊 MUTREK Visual Documentation

Folder ini berisi diagram dan visualisasi untuk dokumentasi MUTREK.

## 📁 File Contents

### 1. **version-timeline.mmd**
Timeline perkembangan MUTREK dari v1.0 hingga v2.2.0
- **Type**: Mermaid Timeline
- **Shows**: Feature evolution per version
- **Colors**: Progressive improvement visual

### 2. **bank-accuracy-chart.mmd**
Chart akurasi processing per bank dan format
- **Type**: Mermaid Graph
- **Shows**: Accuracy rates untuk 7+ banks, 4 formats, 2 detection methods
- **Colors**: Green (100%), Yellow (95-99%), Orange (70-90%)

### 3. **architecture-diagram.mmd**
Arsitektur sistem MUTREK
- **Type**: Mermaid Flow Diagram
- **Shows**: 
  - Access Layer (Web + Bot)
  - Backend API (Flask)
  - Processing Layer (8 processors)
  - Storage (uploads, outputs, bot_temp)
  - Output Modes (4 modes)

### 4. **feature-comparison.mmd**
Perbandingan fitur v1.0 vs v2.0 vs v2.2
- **Type**: Mermaid Comparison Graph
- **Shows**: Evolution dari basic (v1.0) ke advanced (v2.2)
- **Metrics**: Banks, Formats, Modes, Upload, UI, Access

### 5. **processing-modes.mmd**
Penjelasan 4 processing modes
- **Type**: Mermaid Flowchart
- **Shows**: 
  - Full Scan → full_scan_*.xlsx
  - Daily Balance → daily_balance_*.xlsx
  - IDEB SLIK → ideb_slik_*.xlsx
  - Angsuran KOP → angsuran_kop_*.xlsx

---

## 🎨 How to Generate Images

### Option 1: Batch Script (Easiest - Windows) ⭐ RECOMMENDED
```bash
cd docs/images

# For PNG files (transparent background)
generate-all.bat

# Or use PowerShell for better output
generate-all.ps1

# For SVG files (scalable vector)
generate-all-svg.ps1
```

**This will generate all 7 diagrams automatically!**

### Option 2: Manual Command (One by One)
```bash
cd docs/images

# Generate each diagram manually
mmdc -i version-timeline.mmd -o version-timeline.png -b transparent
mmdc -i bank-accuracy-chart.mmd -o bank-accuracy-chart.png -b transparent
mmdc -i architecture-diagram.mmd -o architecture-diagram.png -b transparent
mmdc -i feature-comparison.mmd -o feature-comparison.png -b transparent
mmdc -i processing-modes.mmd -o processing-modes.png -b transparent
mmdc -i statistics-dashboard.mmd -o statistics-dashboard.png -b transparent
mmdc -i user-workflow.mmd -o user-workflow.png -b transparent
```

### Option 3: Mermaid Live Editor (No CLI Needed)
1. Go to https://mermaid.live
2. Copy paste content dari file .mmd
3. Klik "Actions" → "PNG" atau "SVG"
4. Download dan save ke folder ini

### Option 4: VS Code Extension
1. Install extension "Markdown Preview Mermaid Support"
2. Buka file .mmd di VS Code
3. Right click → "Preview Mermaid Diagram"
4. Screenshot atau export

### Option 5: GitHub Auto-Render
- GitHub otomatis render Mermaid di markdown files
- Cukup include di README.md:
  \`\`\`mermaid
  ... paste content here ...
  \`\`\`

---

## 🤖 AI Image Generation Prompts

Jika ingin generate gambar dengan AI (DALL-E, Midjourney, Stable Diffusion):

### 1. **Version Timeline Infographic**
```
Create a modern dark-themed horizontal timeline infographic showing software evolution from v1.0 to v2.2.0. 
Use neon green (#b4ff00) as primary color. Show 4 major versions with icons:
- v1.0: Single bank icon, basic
- v2.0: Multiple bank icons (7), batch files, 3D elements
- v2.1: Balance scales icon, 100% accuracy badge
- v2.2: Robot icon (Telegram bot), projection charts, 4 mode icons
Tech style, dark background, glowing elements, professional.
```

### 2. **Bank Accuracy Chart**
```
Create a dark-themed bar chart or radar chart showing bank processing accuracy rates. 
7 banks on X-axis: BSI (100%), Mandiri (99%), BRI (98%), BNI (97%), BCA (98%), Bank Kalsel (99%), Byond (97%).
Use color coding: Green for 100%, Light green for 95-99%, Yellow for 90-94%.
Modern fintech style, neon green accents (#b4ff00), dark background.
Include format icons: CSV, PDF, Excel, Image with their accuracy rates.
Professional, clean, tech-style visualization.
```

### 3. **System Architecture Diagram**
```
Create a modern system architecture diagram for a bank statement processing app.
Dark theme with neon green accents (#b4ff00).
Layers from top to bottom:
1. Access Layer: Web browser icon + Telegram bot icon
2. API Layer: Flask/Python server
3. Processing Layer: 7+ bank processor modules in grid
4. Storage Layer: Cloud/database icons
5. Output Layer: 4 different Excel file types
Use connecting lines, arrows showing data flow, modern tech style, professional.
```

### 4. **Feature Evolution Comparison**
```
Create a comparison table/infographic showing software evolution across 3 versions.
Dark background, neon green highlights.
3 columns: v1.0 (red), v2.0 (cyan), v2.2 (green)
6 rows comparing:
- Banks supported (1 → 7 → 7+)
- File formats (1 → 4 → 4)
- Processing modes (1 → 2 → 4)
- Upload capability (single → batch → batch+filter)
- UI design (basic → 3D → 3D+modal)
- Access methods (web → web → web+bot)
Use icons, arrows showing growth, modern tech aesthetic.
```

### 5. **4 Processing Modes Flowchart**
```
Create a flowchart showing 4 different processing modes for bank statements.
Dark theme, each mode has unique color:
1. Full Scan (purple) - detailed analysis icon
2. Daily Balance (cyan) - calendar icon
3. IDEB SLIK (yellow) - credit/loan icon
4. Angsuran KOP (green) - projection/chart icon
Start with upload icon at top, branches to 4 modes, each shows output file type.
Modern, clean, professional fintech style, dark background.
```

### 6. **Bot Telegram Feature Showcase**
```
Create a modern infographic showing Telegram bot features.
Dark background, neon green accent (#b4ff00).
Center: Large Telegram bot icon with "MURENA" branding.
Around it, 6-8 feature bubbles:
- "7+ Banks" with bank icons
- "Auto-processing" with gear icon
- "4 Modes" with mode icons
- "Excel/CSV output" with file icons
- "24/7 LIVE" with checkmark
- "Mobile access" with phone icon
Modern, tech-style, glowing elements, professional.
```

### 7. **Accuracy Before/After Comparison**
```
Create a before/after comparison showing accuracy improvement.
Split screen, dark background:
LEFT (v2.0 - Keyword-based): 95-98% accuracy, some transactions missed (red X marks)
RIGHT (v2.1 - Balance-based): 100% accuracy, all transactions captured (green checkmarks)
Use balance scale visual, transaction icons, percentage badges.
Modern fintech style, neon green for improvements, professional visualization.
```

### 8. **Smart Output Naming Visual**
```
Create an infographic showing smart file naming system.
Dark background, 4 file icons with different colors:
1. daily_balance_*.xlsx (cyan) - calendar icon
2. ideb_slik_*.xlsx (yellow) - credit icon  
3. angsuran_kop_*.xlsx (green) - projection icon
4. full_scan_*.xlsx (purple) - analysis icon
Show timestamp pattern, clean modern design, tech aesthetic.
```

---

## 📐 Recommended Image Specifications

### For Documentation
- **Format**: PNG with transparent background
- **Resolution**: 1920x1080 (or higher for print)
- **DPI**: 300 for print, 72 for web
- **Color Mode**: RGB
- **Style**: Dark theme, neon accents, modern tech aesthetic

### For GitHub README
- **Format**: PNG or SVG
- **Max Width**: 1200px (GitHub optimal)
- **File Size**: < 1MB per image
- **Alt Text**: Always include for accessibility

### Color Palette
- **Primary**: #b4ff00 (Neon Green)
- **Secondary**: #667eea (Purple)
- **Accent 1**: #4ecdc4 (Cyan)
- **Accent 2**: #f7b731 (Yellow)
- **Background**: #1a1a1a (Dark)
- **Text**: #ffffff (White)

---

## 📝 Usage in README.md

Add these to main README.md:

```markdown
## 📊 Visual Overview

### Version Timeline
![Version Timeline](docs/images/version-timeline.png)

### Bank Accuracy Rates
![Bank Accuracy](docs/images/bank-accuracy-chart.png)

### System Architecture
![Architecture](docs/images/architecture-diagram.png)

### Feature Evolution
![Feature Comparison](docs/images/feature-comparison.png)

### Processing Modes
![Processing Modes](docs/images/processing-modes.png)
```

---

## 🎯 Priority Order

Generate in this order for best documentation impact:

1. **processing-modes.mmd** - Most useful for users
2. **bank-accuracy-chart.mmd** - Shows reliability
3. **architecture-diagram.mmd** - Technical overview
4. **version-timeline.mmd** - Historical context
5. **feature-comparison.mmd** - Evolution story

---

## 📞 Notes

- All .mmd files are Mermaid syntax compatible
- Can be rendered directly in GitHub markdown
- VS Code can preview with proper extension
- Can be converted to PNG/SVG with tools above

---

**Generated**: September 14, 2026  
**MUTREK Version**: 2.2.0
