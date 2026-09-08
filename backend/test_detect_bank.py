"""Test bank detection for the failed BCA file"""
import sys
sys.path.insert(0, 'processors')

from bank_detector import detect_bank

pdf_path = r'uploads\ESTATEMENT-7326292057-052026-10-13-39.pdf'

print("=" * 80)
print("Testing Bank Detection")
print("=" * 80)

bank = detect_bank(pdf_path, 'pdf')

print(f"\nDetected bank: {bank}")
print(f"Expected: BYOND (based on text analysis)")
