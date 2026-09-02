# -*- coding: utf-8 -*-
"""
Debug OCR output to see what text is being extracted
"""
import os
from processors.mandiri_rk_ocr_processor import extract_images_from_pdf, ocr_image

TEST_FILE = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\Rekening koran bdk 2025.pdf'

print("Extracting and OCR'ing first page...")
images = extract_images_from_pdf(TEST_FILE)

if images:
    first_page = images[0]['image']
    print(f"Image size: {first_page.size}")
    
    text = ocr_image(first_page)
    
    print(f"\nOCR Output ({len(text)} chars):")
    print("=" * 80)
    print(text)
    print("=" * 80)
    
    # Save to file for analysis
    with open('ocr_output_debug.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    
    print("\nSaved to: ocr_output_debug.txt")
    
    # Show lines
    lines = text.split('\n')
    print(f"\nTotal lines: {len(lines)}")
    print("\nFirst 30 lines:")
    for i, line in enumerate(lines[:30], 1):
        if line.strip():
            print(f"{i:3d}: {line}")
