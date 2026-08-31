"""
Fix indentation in mandiri_processor.py
"""

with open('processors/mandiri_processor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line "# Process ALL pages for transactions"
# Everything from that line until "except Exception as password_error:" needs +4 spaces

start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if '# Process ALL pages for transactions' in line:
        start_idx = i
    if start_idx is not None and 'except Exception as password_error:' in line:
        end_idx = i
        break

if start_idx and end_idx:
    print(f"Found section to indent: lines {start_idx+1} to {end_idx}")
    
    # Add 4 spaces to each line in this range
    for i in range(start_idx, end_idx):
        if lines[i].strip():  # Only add indent to non-empty lines
            lines[i] = '    ' + lines[i]
    
    # Write back
    with open('processors/mandiri_processor.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✓ Fixed indentation!")
else:
    print(f"❌ Could not find markers")
