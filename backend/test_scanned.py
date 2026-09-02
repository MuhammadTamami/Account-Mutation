# -*- coding: utf-8 -*-
"""
Test scanned PDF with improved error message
"""
from processors.mandiri_rk_ocr_processor import process_mandiri_rk_ocr_file

filepath = r'c:\Users\muham\Desktop\BSI Excel Convert\test_data\Rekening Koran BDK Jan - Juli 2026.pdf'

try:
    df = process_mandiri_rk_ocr_file(filepath, 'pdf')
    print(f"\n✅ Success: {len(df)} transactions")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
