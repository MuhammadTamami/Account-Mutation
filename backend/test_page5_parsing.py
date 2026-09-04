"""Test parsing page 5 transaction"""
import re

# Data from page 5
test_lines = [
    "Account Statement",
    "Created 30 Jun 2026 10:56:41",
    "00 Bunga 03101 - 0.00 159,475.25 295,162,850.73",
    "31/03/2026 23:59:",
    "Pajak 03101 - 31,895.05 0.00 295,130,955.68",
    "00",
    "For further questions, visit Kopra by Mandiri Help Center: koprabymandiri.com/help Page 5 of 5"
]

print("Testing line-by-line:")
print("=" * 80)

for i, line in enumerate(test_lines):
    print(f"\nLine {i}: {line}")
    
    # Test FORMAT 1 regex
    date_time_match = re.match(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}):?(\d{2})?', line)
    if date_time_match:
        print(f"  ✓ Matched FORMAT 1!")
        print(f"    Date: {date_time_match.group(1)}")
        print(f"    Time: {date_time_match.group(2)}")
        print(f"    Seconds: {date_time_match.group(3)}")
        
        # Check rest of line
        rest_of_line = line[date_time_match.end():].strip()
        print(f"    Rest: '{rest_of_line}'")
        
        # Check for numbers on same line
        numbers_same_line = re.findall(r'[\d,]+\.[\d]{2}', rest_of_line)
        print(f"    Numbers on same line: {numbers_same_line}")
    
    # Check for numbers (amounts)
    numbers = re.findall(r'[\d,]+\.[\d]{2}', line)
    if numbers:
        print(f"  Numbers found: {numbers}")
        if len(numbers) >= 3:
            print(f"    → This looks like debit/credit/balance pattern!")
            print(f"       Debit: {numbers[-3]}")
            print(f"       Credit: {numbers[-2]}")
            print(f"       Balance: {numbers[-1]}")

print("\n" + "=" * 80)
print("ISSUE FOUND:")
print("=" * 80)
print("Line 2: '00 Bunga 03101 - 0.00 159,475.25 295,162,850.73'")
print("  → This has all 3 amounts but no date!")
print("\nLine 3: '31/03/2026 23:59:'")
print("  → This has the date but no amounts!")
print("\nThe date comes AFTER the transaction detail line!")
print("This is REVERSE order compared to other transactions.")
