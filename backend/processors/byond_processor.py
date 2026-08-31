"""
Byond Bank Statement Processor
Supports CSV, PDF, and Excel formats for Byond (BSI digital banking app)
"""
import pandas as pd
import pdfplumber
import re

from processors.bsi_processor import format_indonesian_number

BYOND_MONTHS = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'mei': '05', 'jun': '06', 'jul': '07', 'agu': '08',
    'sep': '09', 'okt': '10', 'nov': '11', 'des': '12',
}


def clean_amount(amount_str):
    """Convert Byond amount format to float (dot=thousand, comma=decimal)."""
    if pd.isna(amount_str) or amount_str == '' or amount_str == '-':
        return 0.0

    amount_str = str(amount_str).strip()
    amount_str = amount_str.replace('Rp', '').replace('IDR', '').strip()

    if amount_str in ['0,00', '0.00', '0']:
        return 0.0

    is_negative = amount_str.startswith('-')
    if is_negative:
        amount_str = amount_str[1:]

    if ',' in amount_str and '.' in amount_str:
        last_comma = amount_str.rfind(',')
        last_dot = amount_str.rfind('.')
        if last_comma > last_dot:
            amount_str = amount_str.replace('.', '').replace(',', '.')
        else:
            amount_str = amount_str.replace(',', '')
    elif ',' in amount_str:
        if len(amount_str.split(',')[-1]) <= 2:
            amount_str = amount_str.replace(',', '.')
        else:
            amount_str = amount_str.replace(',', '')
    elif '.' in amount_str:
        parts = amount_str.split('.')
        if len(parts[-1]) == 3 and len(parts) > 1:
            amount_str = amount_str.replace('.', '')

    try:
        value = float(amount_str)
        return -value if is_negative else value
    except ValueError:
        return 0.0


def parse_byond_datetime(date_time_str):
    """Parse Byond datetime formats like '01 Mar 2026\\n10:33' or '01 Mei 2026 04:22'."""
    if pd.isna(date_time_str) or not str(date_time_str).strip():
        return pd.NaT, pd.NaT

    normalized = ' '.join(str(date_time_str).replace('\n', ' ').split())
    parts = normalized.split(' ')
    if len(parts) < 3:
        return pd.NaT, pd.NaT

    day = parts[0].zfill(2)
    month = BYOND_MONTHS.get(parts[1].lower()[:3])
    year = parts[2]
    time_part = parts[3] if len(parts) > 3 else '00:00:00'
    if len(time_part) == 5:
        time_part = f"{time_part}:00"

    if not month:
        return pd.NaT, pd.NaT

    try:
        datetime_obj = pd.to_datetime(f"{year}-{month}-{day} {time_part}")
        date_obj = pd.to_datetime(f"{year}-{month}-{day}")
        return date_obj, datetime_obj
    except Exception:
        return pd.NaT, pd.NaT


def extract_account_info(text):
    """Extract account metadata from Byond PDF header."""
    if not text:
        return None

    account_info = {}

    name_match = re.search(r'^([A-Z][A-Z0-9 ]{1,60}?)\s+LAPORAN REKENING', text, re.MULTILINE)
    if name_match:
        account_info['name'] = name_match.group(1).strip()

    account_match = re.search(
        r'(?:EASY WADIAH|BYOND)\s*-\s*IDR\s*-\s*(\d+)',
        text,
        re.IGNORECASE,
    )
    if account_match:
        account_info['accountNumber'] = account_match.group(1).strip()

    product_match = re.search(r'(EASY WADIAH)\s*-\s*IDR', text, re.IGNORECASE)
    if product_match:
        account_info['product'] = product_match.group(1).strip()

    period_match = re.search(
        r'PERIODE LAPORAN\s*:\s*(\d{1,2}\s+\w{3})\s*-\s*(\d{1,2}\s+\w{3}\s+\d{4})',
        text,
        re.IGNORECASE,
    )
    if period_match:
        account_info['periodStart'] = period_match.group(1).strip()
        account_info['periodEnd'] = period_match.group(2).strip()

    opening_balance_match = re.search(
        r'SALDO BULAN LALU[\s\S]{0,80}?Rp\s*([\d.,]+)',
        text,
        re.IGNORECASE,
    )
    if opening_balance_match:
        account_info['openingBalance'] = clean_amount(opening_balance_match.group(1))

    return account_info or None


def process_byond_table_rows(table):
    """Parse one extracted Byond transaction table."""
    rows = []
    if not table or len(table) < 2:
        return rows

    header = [str(cell or '').lower() for cell in table[0]]
    header_text = ' '.join(header)
    if 'detail transaksi' not in header_text or 'no reff' not in header_text:
        return rows

    for row in table[1:]:
        if not row or len(row) < 6:
            continue

        date_time_raw, description_raw, reference_raw, debit_raw, credit_raw, balance_raw = row[:6]
        if not date_time_raw:
            continue

        date_obj, datetime_obj = parse_byond_datetime(date_time_raw)
        if pd.isna(date_obj) or pd.isna(datetime_obj):
            continue

        description = ' '.join(str(description_raw or '').split())
        reference = ' '.join(str(reference_raw or '').split())
        debit = clean_amount(debit_raw)
        credit = clean_amount(credit_raw)
        balance = clean_amount(balance_raw)

        if credit > 0 and debit == 0:
            transaction_type = 'Credit'
            amount = credit
        elif debit > 0 and credit == 0:
            transaction_type = 'Debit'
            amount = debit
        else:
            continue

        rows.append({
            'DateTime': datetime_obj,
            'OriginalIndex': len(rows),
            'Date': date_obj,
            'Reference': reference or '-',
            'Description': description,
            'Type': transaction_type,
            'Amount': format_indonesian_number(amount),
            'Balance': format_indonesian_number(balance),
        })

    return rows


def process_byond_pdf(filepath):
    """Process Byond PDF e-statement format."""
    try:
        output_data = []
        account_info = None

        with pdfplumber.open(filepath) as pdf:
            print(f"Processing Byond PDF: {len(pdf.pages)} pages")

            if pdf.pages:
                first_text = pdf.pages[0].extract_text() or ''
                account_info = extract_account_info(first_text)
                if account_info:
                    print(
                        f"Account: {account_info.get('name', '?')} "
                        f"({account_info.get('accountNumber', '?')})"
                    )

            for page in pdf.pages:
                for table in page.extract_tables() or []:
                    output_data.extend(process_byond_table_rows(table))

        if not output_data:
            print("No transactions found in Byond PDF")
            return pd.DataFrame()

        print(f"Extracted {len(output_data)} transactions")

        result_df = pd.DataFrame(output_data)
        result_df = result_df.sort_values(['DateTime', 'OriginalIndex']).reset_index(drop=True)
        result_df = result_df.drop(columns=['DateTime', 'OriginalIndex'])

        if account_info:
            result_df.attrs['account_info'] = account_info

        return result_df

    except Exception as e:
        print(f"Error processing Byond PDF: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def process_byond_csv(filepath):
    """Process Byond CSV export if available."""
    try:
        for sep in [',', ';', '\t']:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, sep=sep, encoding=encoding)
                    if len(df.columns) >= 5:
                        return process_byond_dataframe(df)
                except Exception:
                    continue
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing Byond CSV: {e}")
        return pd.DataFrame()


def process_byond_excel(filepath):
    """Process Byond Excel export if available."""
    try:
        df = pd.read_excel(filepath)
        return process_byond_dataframe(df)
    except Exception as e:
        print(f"Error processing Byond Excel: {e}")
        return pd.DataFrame()


def process_byond_dataframe(df):
    """Process Byond dataframe from CSV/Excel exports."""
    output_data = []

    columns = {str(col).lower(): col for col in df.columns}

    def find_column(*keywords):
        for keyword in keywords:
            for col_lower, col in columns.items():
                if keyword in col_lower:
                    return col
        return None

    date_col = find_column('date & time', 'tanggal', 'date', 'tgl')
    desc_col = find_column('detail transaksi', 'deskripsi', 'keterangan', 'description')
    ref_col = find_column('no reff', 'no referensi', 'referensi', 'reference')
    debit_col = find_column('debit', 'debet')
    credit_col = find_column('kredit', 'credit')
    balance_col = find_column('saldo', 'balance')

    if not date_col:
        return pd.DataFrame()

    for idx, row in df.iterrows():
        if pd.isna(row.get(date_col)):
            continue

        date_obj, datetime_obj = parse_byond_datetime(row.get(date_col))
        if pd.isna(date_obj):
            continue

        debit = clean_amount(row.get(debit_col, 0)) if debit_col else 0
        credit = clean_amount(row.get(credit_col, 0)) if credit_col else 0
        balance = clean_amount(row.get(balance_col, 0)) if balance_col else 0

        if credit > 0:
            transaction_type = 'Credit'
            amount = credit
        elif debit > 0:
            transaction_type = 'Debit'
            amount = debit
        else:
            continue

        output_data.append({
            'DateTime': datetime_obj,
            'OriginalIndex': idx,
            'Date': date_obj,
            'Reference': str(row.get(ref_col, '-')) if ref_col else '-',
            'Description': str(row.get(desc_col, '')) if desc_col else '',
            'Type': transaction_type,
            'Amount': format_indonesian_number(amount),
            'Balance': format_indonesian_number(balance),
        })

    if not output_data:
        return pd.DataFrame()

    result_df = pd.DataFrame(output_data)
    result_df = result_df.sort_values(['DateTime', 'OriginalIndex']).reset_index(drop=True)
    return result_df.drop(columns=['DateTime', 'OriginalIndex'])


def process_byond_file(filepath, file_ext):
    """Main entry point for Byond processor."""
    if file_ext == 'csv':
        return process_byond_csv(filepath)
    if file_ext == 'pdf':
        return process_byond_pdf(filepath)
    if file_ext in ['xlsx', 'xls']:
        return process_byond_excel(filepath)
    return pd.DataFrame()
