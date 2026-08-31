from processors.ideb_processor import process_ideb_pdf

print('=== Testing IDEB SLIK PDF Processor ===\n')

df = process_ideb_pdf('../test_data/IDEB PUTRI MAYA.pdf')

print(f'\n✓ Extracted: {len(df)} credits')

if len(df) > 0:
    print('\n=== IDEB SLIK Data ===')
    print(df.to_string(index=False))
    
    print(f'\n=== Column Details ===')
    for col in df.columns:
        print(f'{col}:')
        print(df[col].to_list())
        print()
else:
    print('❌ No data extracted')
