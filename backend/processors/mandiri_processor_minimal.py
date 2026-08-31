"""
MINIMAL Mandiri Processor - Temporary fix
Just enough to make imports work
"""
import pdfplumber
import pandas as pd
import re
from datetime import datetime

def clean_amount(amount_str):
    """Convert number format to float"""
    if not amount_str or amount_str == '-':
        return 0.0
    
    amount_str = str(amount_str).strip().replace('Rp', '').strip()
    
    if ',' in amount_str and '.' in amount_str:
        last_comma_pos = amount_str.rfind(',')
        last_dot_pos = amount_str.rfind('.')
        
        if last_dot_pos > last_comma_pos:
            amount_str = amount_str.replace(',', '')
        else:
            amount_str = amount_str.replace('.', '').replace(',', '.')
    elif ',' in amount_str:
        last_comma_pos = amount_str.rfind(',')
        if len(amount_str) - last_comma_pos <= 3:
            amount_str = amount_str.replace(',', '.')
        else:
            amount_str = amount_str.replace(',', '')
    elif '.' in amount_str:
        last_dot_pos = amount_str.rfind('.')
        if len(amount_str) - last_dot_pos > 3:
            amount_str = amount_str.replace('.', '')
    
    try:
        return float(amount_str)
    except:
        return 0.0

def format_indonesian_number(value):
    """Format number as Indonesian format"""
    if pd.isna(value) or value == 0:
        return "0,00"
    
    formatted = f"{value:.2f}"
    parts = formatted.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    integer_with_sep = f"{int(integer_part):,}"
    return f"{integer_with_sep},{decimal_part}"

def process_mandiri_csv(filepath):
    """Process Mandiri CSV - minimal implementation"""
    return pd.DataFrame()

def process_mandiri_pdf(filepath, pdf_password=''):
    """Process Mandiri PDF - minimal implementation for now"""
    # TODO: Restore full implementation
    # For now, return empty to allow other processors to work
    print("⚠ Mandiri PDF processor temporarily disabled - under maintenance")
    return pd.DataFrame()

def process_mandiri_excel(filepath):
    """Process Mandiri Excel - minimal implementation"""
    return pd.DataFrame()

def process_mandiri_file(filepath, file_ext, pdf_password=''):
    """Main entry point"""
    if file_ext == 'csv':
        return process_mandiri_csv(filepath)
    elif file_ext == 'pdf':
        return process_mandiri_pdf(filepath, pdf_password)
    elif file_ext in ['xlsx', 'xls']:
        return process_mandiri_excel(filepath)
    else:
        return pd.DataFrame()
