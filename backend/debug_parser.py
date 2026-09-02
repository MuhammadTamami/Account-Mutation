# -*- coding: utf-8 -*-
"""
Debug parser to see why lines are not matching
"""
from processors.mandiri_rk_ocr_processor import parse_ocr_text_line

# Sample OCR lines from debug output
test_lines = [
    "[2aRAKAT Goa KUiTAN [s00183sse66_anzsai.21 —fizsas0 [eon | —alsaatiior ta [kr anisa auaranian | \"sro. oo | sansie ry",
    "[panaxar 8 urran [a100393s8e06 [2025-0822 | aas20 ——|euar | —al saat or [ore anna auarawan | -sopmaceao | —aoaieoas 18]",
    "[aanacat Don xuitan [210019555666 [2025-03-26 —|auso:aa aaa | [beast inc-cs | poasonpabrnaoianivo5550060 | \"wag, 000.00 | nis: 18|",
    "[saraxat Doa xoiTan_[aiooassssees [2035 02-06 [ow:soa4 [poss | ws] rast ne cs Je anrsmaaseninosantooaneaesarsa | 250,000900.00| #70375 77520]",
    "[BaRAKAT DOA xuITAN [ai00i95ssees_[pozs02-07 —[oo.b:s8 [zoe ws] Fast ne ics —[e__jossmaaremmoniooamenrisce | 220,009000.00]] —750375.77.20]",
]

print("Testing parser on sample lines:\n")
print("=" * 80)

for i, line in enumerate(test_lines, 1):
    print(f"\nLine {i}:")
    print(f"Input: {line[:100]}...")
    
    result = parse_ocr_text_line(line)
    
    if result:
        print(f"✓ MATCHED!")
        print(f"  Date: {result['Date']}")
        print(f"  Type: {result['Type']}")
        print(f"  Amount: {result['Amount']}")
        print(f"  Balance: {result['Balance']}")
        print(f"  Description: {result['Description'][:50]}")
    else:
        print(f"✗ NOT MATCHED")
        
        # Debug why
        if '|' in line:
            parts = line.split('|')
            print(f"  Pipe parts: {len(parts)}")
            if len(parts) >= 3:
                print(f"  Last part (balance): {parts[-1][:30]}")
                print(f"  2nd last (amount): {parts[-2][:30]}")
        
        # Check for dates
        import re
        dates_yyyy = re.findall(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', line)
        dates_dd = re.findall(r'(\d{1,2}/\d{1,2}/\d{2,4})', line)
        print(f"  YYYY-MM-DD dates found: {dates_yyyy}")
        print(f"  DD/MM/YY dates found: {dates_dd}")

print("\n" + "=" * 80)
