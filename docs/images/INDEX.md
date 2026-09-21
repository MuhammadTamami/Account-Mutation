# 📊 MUTREK Visual Documentation Index

Quick navigation untuk semua diagram dan visualisasi.

## 🎯 Quick Links

| Diagram | Description | Use Case | Priority |
|---------|-------------|----------|----------|
| [Processing Modes](processing-modes.mmd) | 4 mode processing flowchart | User guide | ⭐⭐⭐⭐⭐ |
| [Bank Accuracy](bank-accuracy-chart.mmd) | Accuracy comparison per bank | Marketing | ⭐⭐⭐⭐⭐ |
| [Architecture](architecture-diagram.mmd) | System architecture | Technical docs | ⭐⭐⭐⭐ |
| [User Workflow](user-workflow.mmd) | Web vs Bot workflow | User guide | ⭐⭐⭐⭐ |
| [Statistics](statistics-dashboard.mmd) | Overall stats dashboard | Marketing | ⭐⭐⭐⭐ |
| [Version Timeline](version-timeline.mmd) | Development timeline | Release notes | ⭐⭐⭐ |
| [Feature Comparison](feature-comparison.mmd) | v1.0 vs v2.0 vs v2.2 | Changelog | ⭐⭐⭐ |

## 📁 File Structure

```
docs/images/
├── README.md                      # Main documentation & prompts
├── INDEX.md                       # This file - Quick navigation
├── version-timeline.mmd           # Development timeline
├── bank-accuracy-chart.mmd        # Accuracy rates per bank
├── architecture-diagram.mmd       # System architecture
├── feature-comparison.mmd         # Version comparison
├── processing-modes.mmd           # 4 modes flowchart
├── statistics-dashboard.mmd       # Overall statistics
└── user-workflow.mmd             # User journey (Web vs Bot)
```

## 🎨 Diagram Categories

### 1. User-Facing (For End Users)
- ✅ **processing-modes.mmd** - How to use each mode
- ✅ **user-workflow.mmd** - Step-by-step guide

### 2. Marketing & Sales
- ✅ **bank-accuracy-chart.mmd** - Show reliability
- ✅ **statistics-dashboard.mmd** - Show capabilities
- ✅ **feature-comparison.mmd** - Show evolution

### 3. Technical Documentation
- ✅ **architecture-diagram.mmd** - System design
- ✅ **version-timeline.mmd** - Development history

## 🔄 Generation Status

| File | Mermaid | PNG | SVG | Status |
|------|---------|-----|-----|--------|
| version-timeline.mmd | ✅ | ⏳ | ⏳ | Ready to generate |
| bank-accuracy-chart.mmd | ✅ | ⏳ | ⏳ | Ready to generate |
| architecture-diagram.mmd | ✅ | ⏳ | ⏳ | Ready to generate |
| feature-comparison.mmd | ✅ | ⏳ | ⏳ | Ready to generate |
| processing-modes.mmd | ✅ | ⏳ | ⏳ | Ready to generate |
| statistics-dashboard.mmd | ✅ | ⏳ | ⏳ | Ready to generate |
| user-workflow.mmd | ✅ | ⏳ | ⏳ | Ready to generate |

Legend: ✅ Done | ⏳ Pending | ❌ Not started

## 📐 Usage Examples

### In Main README.md
```markdown
## 📊 Visual Overview

### How It Works
![Processing Modes](docs/images/processing-modes.png)

### Bank Support & Accuracy
![Bank Accuracy](docs/images/bank-accuracy-chart.png)

### System Architecture
![Architecture](docs/images/architecture-diagram.png)
```

### In CHANGELOG.md
```markdown
## Version History

![Version Timeline](docs/images/version-timeline.png)

## Feature Evolution

![Feature Comparison](docs/images/feature-comparison.png)
```

### In User Guide
```markdown
## Getting Started

Choose your preferred method:

![User Workflow](docs/images/user-workflow.png)
```

## 🛠️ Generate All Images

### Using Mermaid CLI (Recommended)
```bash
cd docs/images

# Generate PNG (for web/docs)
mmdc -i version-timeline.mmd -o version-timeline.png -b transparent
mmdc -i bank-accuracy-chart.mmd -o bank-accuracy-chart.png -b transparent
mmdc -i architecture-diagram.mmd -o architecture-diagram.png -b transparent
mmdc -i feature-comparison.mmd -o feature-comparison.png -b transparent
mmdc -i processing-modes.mmd -o processing-modes.png -b transparent
mmdc -i statistics-dashboard.mmd -o statistics-dashboard.png -b transparent
mmdc -i user-workflow.mmd -o user-workflow.png -b transparent

# Generate SVG (scalable)
mmdc -i version-timeline.mmd -o version-timeline.svg
mmdc -i bank-accuracy-chart.mmd -o bank-accuracy-chart.svg
mmdc -i architecture-diagram.mmd -o architecture-diagram.svg
mmdc -i feature-comparison.mmd -o feature-comparison.svg
mmdc -i processing-modes.mmd -o processing-modes.svg
mmdc -i statistics-dashboard.mmd -o statistics-dashboard.svg
mmdc -i user-workflow.mmd -o user-workflow.svg
```

### Using Mermaid Live
1. Go to https://mermaid.live
2. Copy content dari file .mmd
3. Klik "Actions" → Download PNG/SVG
4. Save dengan nama yang sama

### Batch Convert Script
```bash
# Save as generate-all.sh
#!/bin/bash
for file in *.mmd; do
    base="${file%.mmd}"
    mmdc -i "$file" -o "$base.png" -b transparent
    mmdc -i "$file" -o "$base.svg"
    echo "✅ Generated: $base.png and $base.svg"
done
```

## 🎯 Next Steps

1. **Generate Images**:
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   cd docs/images
   # Run generate commands above
   ```

2. **Add to README**:
   - Copy usage examples above
   - Paste ke main README.md
   - Adjust paths if needed

3. **Update .gitignore**:
   ```gitignore
   # Allow generated images
   !docs/images/*.png
   !docs/images/*.svg
   ```

4. **Commit**:
   ```bash
   git add docs/images/
   git commit -m "docs: Add visual diagrams for MUTREK"
   ```

## 📞 Support

If you need to regenerate or modify diagrams:
1. Edit the .mmd file
2. Re-run mermaid CLI
3. Images will auto-update

---

**Last Updated**: September 14, 2026  
**MUTREK Version**: 2.2.0  
**Total Diagrams**: 7
