import pandas as pd
import glob

files = glob.glob('outputs/test_output_Acc_Statement_*.xlsx')
if files:
    print(f"Checking: {files[0]}")
    df = pd.read_excel(files[0], sheet_name='Saldo Harian', header=None)
    print('\nFull output (rows 25-45):')
    print(df.iloc[25:45])
