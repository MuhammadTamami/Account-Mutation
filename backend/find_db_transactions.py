"""Find DB transactions in BCA PDF"""
import fitz

doc = fitz.open('../test_data/9. April 2026.pdf')

print("Looking for lines with ' DB' suffix...")
print("=" * 80)

found_count = 0
for page_num in range(len(doc)):
    text = doc[page_num].get_text()
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        # Check if line ends with " DB" or has "DB" after amount
        if ' DB' in line:
            found_count += 1
            print(f"\nPage {page_num + 1}, Line {i}:")
            print(f"  [{line}]")
            
            # Show context (2 lines before, 2 lines after)
            print("  Context:")
            for j in range(max(0, i-2), min(len(lines), i+3)):
                marker = ">>>" if j == i else "   "
                print(f"  {marker} {j}: {lines[j]}")
            
            if found_count >= 10:  # Limit output
                break
    
    if found_count >= 10:
        break

print(f"\n" + "=" * 80)
print(f"Found {found_count} lines with ' DB'")

doc.close()
