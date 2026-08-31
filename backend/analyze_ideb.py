import fitz

doc = fitz.open('test_data/IDEB PUTRI MAYA.pdf')

print(f"Total pages: {len(doc)}\n")

# Find page with credit table
for i, page in enumerate(doc):
    text = page.get_text()
    if 'Pelapor' in text and 'Plafon Awal' in text and 'Baki Debet' in text and 'Tanggal Mulai' in text:
        print(f"=== Page {i+1} contains credit table ===\n")
        print(text[:4000])
        print("\n" + "="*80 + "\n")
        break

doc.close()
