from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from processors.bank_detector import detect_bank
from processors.bsi_processor import process_bsi_file
from processors.mandiri_processor import process_mandiri_file
from processors.mandiri_rk_processor import process_mandiri_rk_file
from processors.mandiri_rk_ocr_processor import process_mandiri_rk_ocr_file
from processors.bca_processor import process_bca_file
from processors.bri_processor import process_bri_file
from processors.bni_processor import process_bni_file
from processors.bank_kalsel_processor import process_bank_kalsel_file
from processors.byond_processor import process_byond_file
from processors.ideb_processor import process_ideb_file
from processors.angsuran_processor import process_angsuran_batch, export_to_excel_angsuran

# Try to import image processor, but don't fail if not available
try:
    from processors.image_processor import process_image_file
    IMAGE_PROCESSOR_AVAILABLE = True
except ImportError as e:
    IMAGE_PROCESSOR_AVAILABLE = False
    print(f"Warning: Image processor not available: {e}")
    print("Image upload will be disabled. Install pytesseract and Pillow to enable.")

import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_single_file(filepath, filename, pdf_password=''):
    """Process single file with smart bank detection"""
    file_ext = filename.lower().split('.')[-1]
    
    # Handle image files (OCR)
    if file_ext in ['jpg', 'jpeg', 'png']:
        if not IMAGE_PROCESSOR_AVAILABLE:
            raise Exception('Image processing not available')
        df = process_image_file(filepath)
        file_type = 'Bank Statement Image (OCR)'
        return df, file_type
    
    # Smart bank detection for CSV/PDF/Excel
    bank_name = detect_bank(filepath, file_ext)
    print(f"✓ Detected bank: {bank_name} from {filename} (.{file_ext})")
    
    # Route to appropriate processor with unified interface
    if bank_name == 'BSI':
        df = process_bsi_file(filepath, file_ext)
        file_type = f'BSI {file_ext.upper()}'
    
    elif bank_name == 'MANDIRI':
        df = process_mandiri_file(filepath, file_ext, pdf_password)
        file_type = f'Mandiri {file_ext.upper()}'
    
    elif bank_name == 'MANDIRI_RK':
        df = process_mandiri_rk_file(filepath, file_ext, pdf_password)
        file_type = f'Mandiri RK {file_ext.upper()}'
    
    elif bank_name == 'MANDIRI_RK_OCR':
        df = process_mandiri_rk_ocr_file(filepath, file_ext, pdf_password)
        file_type = f'Mandiri RK OCR {file_ext.upper()}'
    
    elif bank_name == 'BCA':
        df = process_bca_file(filepath, file_ext)
        file_type = f'BCA {file_ext.upper()}'
    
    elif bank_name == 'BRI':
        df = process_bri_file(filepath, file_ext)
        file_type = f'BRI {file_ext.upper()}'
    
    elif bank_name == 'BNI':
        df = process_bni_file(filepath, file_ext)
        file_type = f'BNI {file_ext.upper()}'
    
    elif bank_name == 'BANK_KALSEL':
        df = process_bank_kalsel_file(filepath, file_ext)
        file_type = f'Bank Kalsel {file_ext.upper()}'
    
    elif bank_name == 'BYOND':
        df = process_byond_file(filepath, file_ext)
        file_type = f'Byond {file_ext.upper()}'
    
    elif bank_name == 'IDEB':
        df = process_ideb_file(filepath, file_ext)
        file_type = f'IDEB SLIK {file_ext.upper()}'
    
    else:
        # Unknown bank - try fallback based on extension
        print(f"⚠ Unknown bank, trying fallback for .{file_ext}")
        if file_ext == 'csv':
            # Try BSI format as fallback
            df = process_bsi_file(filepath, file_ext)
            file_type = 'CSV (Unknown Bank - trying BSI format)'
        elif file_ext == 'pdf':
            # Try Mandiri format as fallback
            df = process_mandiri_file(filepath, file_ext, pdf_password)
            file_type = 'PDF (Unknown Bank - trying Mandiri format)'
        elif file_ext in ['xlsx', 'xls']:
            # Try BSI format as fallback
            df = process_bsi_file(filepath, file_ext)
            file_type = 'Excel (Unknown Bank - trying BSI format)'
        else:
            raise Exception(f'Unsupported file type: .{file_ext}')
    
    if df is None or len(df) == 0:
        raise Exception(f'No data extracted from file. Format may not match {bank_name} structure.')
    
    return df, file_type

def process_batch_files(files, pdf_password=''):
    """Process multiple files and combine results"""
    print(f"Processing {len(files)} files in batch mode...")
    
    all_dataframes = []
    processed_files = []
    failed_files = []
    ocr_summaries = []  # Collect OCR summaries from images
    
    for idx, file in enumerate(files):
        if file.filename == '':
            continue
        
        try:
            # Save file
            filename = f"batch_{idx}_{file.filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Process file
            df, file_type = process_single_file(filepath, file.filename, pdf_password)
            
            if df is not None and len(df) > 0:
                # Add source file column
                df['SourceFile'] = file.filename
                all_dataframes.append(df)
                
                # Collect OCR summary if available (from images)
                if 'ocr_summary' in df.attrs:
                    ocr_summaries.append({
                        'filename': file.filename,
                        'summary': df.attrs['ocr_summary']
                    })
                
                processed_files.append({
                    'filename': file.filename,
                    'type': file_type,
                    'records': len(df)
                })
                print(f"[OK] Processed {file.filename}: {len(df)} records")
            else:
                failed_files.append({
                    'filename': file.filename,
                    'error': 'No data found'
                })
                print(f"[FAIL] Failed {file.filename}: No data")
                
        except Exception as e:
            failed_files.append({
                'filename': file.filename,
                'error': str(e)
            })
            print(f"[ERROR] Error {file.filename}: {e}")
            continue
    
    if len(all_dataframes) == 0:
        return jsonify({
            'error': 'No files could be processed',
            'failed_files': failed_files
        }), 400
    
    # Combine all dataframes
    print(f"Combining {len(all_dataframes)} dataframes...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Remove SourceFile column for processing (add back later if needed)
    source_files = combined_df['SourceFile'].copy()
    combined_df_clean = combined_df.drop(columns=['SourceFile'])
    
    # Continue with standard processing
    return process_combined_dataframe(combined_df_clean, source_files, processed_files, failed_files, ocr_summaries)

def process_combined_dataframe(df, source_files, processed_files, failed_files, ocr_summaries=None):
    """Process combined DataFrame and return response"""
    # Convert Amount and Balance back to float for calculations
    def parse_indonesian_number(value):
        if isinstance(value, str):
            value = value.strip().replace('Rp', '').replace(' ', '').strip()
            
            # Handle different formats:
            # 1. Indonesian: 1.234.567,89 (dots for thousands, comma for decimal)
            # 2. International: 1,234,567.89 (commas for thousands, dot for decimal)
            # 3. Mixed: 200.000.000.00 (dots everywhere)
            
            if ',' in value and '.' in value:
                # Both separators present
                last_comma_pos = value.rfind(',')
                last_dot_pos = value.rfind('.')
                
                if last_dot_pos > last_comma_pos:
                    # Format: 1,234,567.89 (International)
                    value = value.replace(',', '')
                else:
                    # Format: 1.234.567,89 (Indonesian)
                    value = value.replace('.', '').replace(',', '.')
            elif ',' in value:
                # Only comma present
                last_comma_pos = value.rfind(',')
                decimal_part_length = len(value) - last_comma_pos - 1
                
                if decimal_part_length == 2:
                    # Format: 1.234.567,89 (Indonesian decimal)
                    value = value.replace('.', '').replace(',', '.')
                else:
                    # Format: 1,234,567 (thousand separator)
                    value = value.replace(',', '')
            elif '.' in value:
                # Only dots present
                last_dot_pos = value.rfind('.')
                decimal_part_length = len(value) - last_dot_pos - 1
                
                if decimal_part_length == 2:
                    # Format: 200.000.000.00 - last dot is decimal
                    value = value[:last_dot_pos].replace('.', '') + '.' + value[last_dot_pos+1:]
                elif decimal_part_length > 3:
                    # Keep as is
                    pass
                else:
                    # All dots are thousand separators
                    value = value.replace('.', '')
            
            try:
                return float(value)
            except Exception as e:
                print(f"⚠ Failed to parse '{value}': {e}")
                return 0.0
        return float(value)
    
    df['Amount_numeric'] = df['Amount'].apply(parse_indonesian_number)
    df['Balance_numeric'] = df['Balance'].apply(parse_indonesian_number)
    
    # Add month column for grouping
    df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')
    df['DateOnly'] = pd.to_datetime(df['Date']).dt.date
    
    # Detect last transaction per day
    df['is_last_of_day'] = False
    for date in df['DateOnly'].unique():
        last_idx = df[df['DateOnly'] == date].index[-1]
        df.loc[last_idx, 'is_last_of_day'] = True
    
    # Daily balance table - strategy depends on bank type
    daily_balance_data = []
    
    # Check if this is BCA (has backdate transactions with "TANGGAL :")
    has_backdate = df['Description'].str.contains('TANGGAL :', case=False, na=False).any()
    
    if has_backdate:
        # BCA Strategy: Use first non-backdate transaction balance
        for date in sorted(df['DateOnly'].unique()):
            day_transactions = df[df['DateOnly'] == date]
            
            balance_value = '0.00'
            
            # Find FIRST non-backdate Debit with balance
            non_backdate_debit = day_transactions[
                (day_transactions['Type'] == 'Debit') & 
                (~day_transactions['Description'].str.contains('TANGGAL :', case=False, na=False)) &
                (day_transactions['Balance'] != '0.00')
            ]
            
            if len(non_backdate_debit) > 0:
                balance_value = non_backdate_debit.iloc[0]['Balance']
            else:
                # Find FIRST non-backdate Credit with balance
                non_backdate_credit = day_transactions[
                    (day_transactions['Type'] == 'Credit') & 
                    (~day_transactions['Description'].str.contains('TANGGAL :', case=False, na=False)) &
                    (day_transactions['Balance'] != '0.00')
                ]
                
                if len(non_backdate_credit) > 0:
                    balance_value = non_backdate_credit.iloc[0]['Balance']
                else:
                    # Fallback: Use first balance (any)
                    non_zero = day_transactions[day_transactions['Balance'] != '0.00']
                    if len(non_zero) > 0:
                        balance_value = non_zero.iloc[0]['Balance']
            
            daily_balance_data.append({
                'Date': day_transactions.iloc[0]['Date'],
                'Balance': balance_value
            })
    else:
        # Other banks (Bank Kalsel, Mandiri, etc.): Use LAST balance of the day
        for date in sorted(df['DateOnly'].unique()):
            day_transactions = df[df['DateOnly'] == date]
            
            balance_value = '0.00'
            
            # Strategy: Get LAST transaction balance (end of day balance)
            non_zero = day_transactions[day_transactions['Balance'] != '0.00']
            
            if len(non_zero) > 0:
                # Use LAST balance (final transaction of the day)
                balance_value = non_zero.iloc[-1]['Balance']
            
            daily_balance_data.append({
                'Date': day_transactions.iloc[0]['Date'],
                'Balance': balance_value
            })
    
    # Monthly summary with frequency counts
    monthly_summary = []
    for month in sorted(df['Month'].unique()):
        month_data = df[df['Month'] == month]
        
        total_debit = month_data[month_data['Type'] == 'Debit']['Amount_numeric'].sum()
        total_credit = month_data[month_data['Type'] == 'Credit']['Amount_numeric'].sum()
        freq_debit = len(month_data[month_data['Type'] == 'Debit'])
        freq_credit = len(month_data[month_data['Type'] == 'Credit'])
        
        from processors.bsi_processor import format_indonesian_number
        
        monthly_summary.append({
            'month': str(month),
            'monthName': month.strftime('%B %Y'),
            'totalDebit': format_indonesian_number(total_debit),
            'totalCredit': format_indonesian_number(total_credit),
            'freqDebit': freq_debit,
            'freqCredit': freq_credit,
            'totalDebitNumeric': float(total_debit),
            'totalCreditNumeric': float(total_credit)
        })
    
    print(f"Monthly summary calculated for {len(monthly_summary)} months")
    
    # All data for display
    all_data = df[['Date', 'Reference', 'Description', 'Type', 'Amount', 'Balance', 'is_last_of_day']].to_dict('records')
    total_records = len(df)
    
    # Summary - check if we have OCR summaries
    has_ocr_summary = ocr_summaries and len(ocr_summaries) > 0
    
    if has_ocr_summary:
        # Try to use OCR summary totals
        print(f"Found {len(ocr_summaries)} OCR summaries")
        total_debit_from_ocr = sum(s['summary'].get('total_debit', 0) or 0 for s in ocr_summaries)
        total_credit_from_ocr = sum(s['summary'].get('total_credit', 0) or 0 for s in ocr_summaries)
        
        if total_debit_from_ocr > 0 or total_credit_from_ocr > 0:
            total_debit = total_debit_from_ocr
            total_credit = total_credit_from_ocr
            balance = total_credit - total_debit
            summary_source = 'OCR Summary (from Images)'
            print(f"Using OCR summary: Debit={total_debit}, Credit={total_credit}")
        else:
            # Fallback to calculation
            total_debit = df[df['Type'] == 'Debit']['Amount_numeric'].sum()
            total_credit = df[df['Type'] == 'Credit']['Amount_numeric'].sum()
            balance = total_credit - total_debit
            summary_source = 'Calculated from Batch Transactions'
    else:
        # Calculate from transactions
        total_debit = df[df['Type'] == 'Debit']['Amount_numeric'].sum()
        total_credit = df[df['Type'] == 'Credit']['Amount_numeric'].sum()
        balance = total_credit - total_debit
        summary_source = 'Calculated from Batch Transactions'
    
    summary = {
        'totalRecords': total_records,
        'totalDebit': float(total_debit),
        'totalCredit': float(total_credit),
        'balance': float(balance),
        'dateRange': {
            'start': df['Date'].min().strftime('%Y-%m-%d'),
            'end': df['Date'].max().strftime('%Y-%m-%d')
        },
        'fileType': f'Batch ({len(processed_files)} files)',
        'summarySource': summary_source,
        'batchInfo': {
            'totalFiles': len(processed_files) + len(failed_files),
            'processed': len(processed_files),
            'failed': len(failed_files),
            'processedFiles': processed_files,
            'failedFiles': failed_files
        }
    }
    
    # Save processed data
    temp_filename = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
    df_output = df[['Date', 'Reference', 'Description', 'Type', 'Amount', 'Balance']]
    df_output.to_csv(temp_path, index=False)
    
    return jsonify({
        'success': True,
        'allData': all_data,
        'dailyBalance': daily_balance_data,
        'monthlySummary': monthly_summary,
        'summary': summary,
        'tempFile': temp_filename,
        'mode': 'batch'
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        # Get password if provided
        pdf_password = request.form.get('password', '')
        
        # First, try to get files from 'files' key (batch mode)
        files = request.files.getlist('files')
        
        # Check if we have valid batch files
        valid_batch_files = [f for f in files if f and f.filename != '']
        
        if len(valid_batch_files) > 1:
            # Multiple files - Batch mode
            print(f"Batch mode: {len(valid_batch_files)} files")
            return process_batch_files(valid_batch_files, pdf_password)
        elif len(valid_batch_files) == 1:
            # Single file from batch input
            file = valid_batch_files[0]
        elif 'file' in request.files:
            # Single file from 'file' key
            file = request.files['file']
            if not file or file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
        else:
            return jsonify({'error': 'No file provided'}), 400
        
        # Save uploaded file (single file mode)
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Auto-detect file type based on extension and content
        file_ext = filename.lower().split('.')[-1]
        
        # Check if file type is supported
        if file_ext not in ['csv', 'pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls']:
            return jsonify({'error': f'Unsupported file type: .{file_ext}. Please upload CSV, PDF, Excel (XLSX/XLS), or Image (JPG/PNG) file.'}), 400
        
        # Process using smart detection
        if file_ext in ['csv', 'pdf', 'xlsx', 'xls']:
            # Smart bank detection
            bank_name = detect_bank(filepath, file_ext)
            print(f"✓ Detected bank: {bank_name} from {filename} (.{file_ext})")
            
            # Route to appropriate processor with unified interface
            if bank_name == 'BSI':
                df = process_bsi_file(filepath, file_ext)
                file_type = f'BSI {file_ext.upper()}'
            
            elif bank_name == 'MANDIRI':
                df = process_mandiri_file(filepath, file_ext, pdf_password)
                file_type = f'Mandiri {file_ext.upper()}'
            
            elif bank_name == 'MANDIRI_RK':
                df = process_mandiri_rk_file(filepath, file_ext, pdf_password)
                file_type = f'Mandiri RK {file_ext.upper()}'
            
            elif bank_name == 'MANDIRI_RK_OCR':
                df = process_mandiri_rk_ocr_file(filepath, file_ext, pdf_password)
                file_type = f'Mandiri RK OCR {file_ext.upper()}'
            
            elif bank_name == 'BCA':
                df = process_bca_file(filepath, file_ext)
                file_type = f'BCA {file_ext.upper()}'
            
            elif bank_name == 'BRI':
                df = process_bri_file(filepath, file_ext)
                file_type = f'BRI {file_ext.upper()}'
            
            elif bank_name == 'BNI':
                df = process_bni_file(filepath, file_ext)
                file_type = f'BNI {file_ext.upper()}'
            
            elif bank_name == 'BANK_KALSEL':
                df = process_bank_kalsel_file(filepath, file_ext)
                file_type = f'Bank Kalsel {file_ext.upper()}'
            
            elif bank_name == 'BYOND':
                df = process_byond_file(filepath, file_ext)
                file_type = f'Byond {file_ext.upper()}'
            
            elif bank_name == 'IDEB':
                df = process_ideb_file(filepath, file_ext)
                file_type = f'IDEB SLIK {file_ext.upper()}'
            
            else:
                # Unknown bank - try fallback
                print(f"⚠ Unknown bank detected for {filename}")
                print(f"ℹ Trying fallback based on extension: .{file_ext}")
                
                if file_ext == 'csv':
                    df = process_bsi_file(filepath, file_ext)
                    file_type = 'CSV (Unknown Bank - using BSI format)'
                elif file_ext == 'pdf':
                    df = process_mandiri_file(filepath, file_ext)
                    file_type = 'PDF (Unknown Bank - using Mandiri format)'
                elif file_ext in ['xlsx', 'xls']:
                    df = process_bsi_file(filepath, file_ext)
                    file_type = 'Excel (Unknown Bank - using BSI format)'
                else:
                    return jsonify({'error': f'Unsupported file format: .{file_ext}'}), 400
        
        elif file_ext in ['jpg', 'jpeg', 'png']:
            # Process as Image (OCR)
            if not IMAGE_PROCESSOR_AVAILABLE:
                return jsonify({
                    'error': 'Image processing tidak tersedia. Pytesseract atau Pillow belum terinstall.',
                    'instruction': 'Install dengan: pip install pytesseract Pillow',
                    'alternative': 'Gunakan file PDF atau CSV untuk akurasi terbaik.'
                }), 400
            
            try:
                df = process_image_file(filepath)
                file_type = 'Bank Statement Image (OCR)'
            except Exception as e:
                error_msg = str(e)
                if 'Tesseract' in error_msg or 'OCR' in error_msg:
                    return jsonify({
                        'error': 'Tesseract OCR belum terinstall.',
                        'instruction': 'Download: https://github.com/UB-Mannheim/tesseract/wiki',
                        'alternative': 'Gunakan file PDF atau CSV untuk akurasi lebih baik.'
                    }), 400
                else:
                    return jsonify({'error': f'Error processing image: {error_msg}'}), 500
        else:
            return jsonify({'error': f'Unsupported file type: .{file_ext}'}), 400
        
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data found in file. Please check the file format.'}), 400
        
        # Special handling for IDEB SLIK (different data structure)
        if bank_name == 'IDEB':
            print(f"✓ Processing IDEB SLIK data: {len(df)} credits")
            
            # Get debitur name from DataFrame attributes
            debitur_name = df.attrs.get('debitur_name', 'Unknown')
            
            # IDEB data structure: Nama Bank, Plafon, Yield (%), O/S, Tanggal Pencairan, Tanggal Jatuh Tempo, Jk Waktu, Kol, Jenis Konsumsi, Angsuran
            # Return as-is without transformation
            ideb_data = df.to_dict('records')
            
            # Save to temp file (also save debitur_name in first line as comment)
            temp_filename = f"ideb_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
            
            # Write debitur name as first line (will be read back later)
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(f"# DEBITUR_NAME:{debitur_name}\n")
                df.to_csv(f, index=False)
            
            return jsonify({
                'success': True,
                'debiturName': debitur_name,
                'mode': 'ideb',
                'data': ideb_data,
                'summary': {
                    'totalRecords': len(df),
                    'fileType': file_type
                },
                'tempFile': temp_filename
            })
        
        # Convert Amount and Balance back to float for calculations
        def parse_indonesian_number(value):
            """Convert Indonesian format string back to float for calculations
            Handles multiple formats:
            - Indonesian: 1.234.567,89 (dots for thousands, comma for decimal)
            - International: 1,234,567.89 (commas for thousands, dot for decimal)
            - Mixed: 200.000.000.00 (dots everywhere)
            """
            if isinstance(value, str):
                value = value.strip().replace('Rp', '').replace(' ', '').strip()
                
                if ',' in value and '.' in value:
                    # Both separators present
                    last_comma_pos = value.rfind(',')
                    last_dot_pos = value.rfind('.')
                    
                    if last_dot_pos > last_comma_pos:
                        # Format: 1,234,567.89 (International)
                        value = value.replace(',', '')
                    else:
                        # Format: 1.234.567,89 (Indonesian)
                        value = value.replace('.', '').replace(',', '.')
                elif ',' in value:
                    # Only comma present
                    last_comma_pos = value.rfind(',')
                    decimal_part_length = len(value) - last_comma_pos - 1
                    
                    if decimal_part_length == 2:
                        # Format: 1.234.567,89 (Indonesian decimal)
                        value = value.replace('.', '').replace(',', '.')
                    else:
                        # Format: 1,234,567 (thousand separator)
                        value = value.replace(',', '')
                elif '.' in value:
                    # Only dots present
                    last_dot_pos = value.rfind('.')
                    decimal_part_length = len(value) - last_dot_pos - 1
                    
                    if decimal_part_length == 2:
                        # Format: 200.000.000.00 - last dot is decimal
                        value = value[:last_dot_pos].replace('.', '') + '.' + value[last_dot_pos+1:]
                    elif decimal_part_length > 3:
                        # Keep as is
                        pass
                    else:
                        # All dots are thousand separators
                        value = value.replace('.', '')
                
                try:
                    return float(value)
                except Exception as e:
                    print(f"⚠ Failed to parse '{value}': {e}")
                    return 0.0
            return float(value)
        
        # Create numeric columns for calculations
        df['Amount_numeric'] = df['Amount'].apply(parse_indonesian_number)
        df['Balance_numeric'] = df['Balance'].apply(parse_indonesian_number)
        
        # Add month column for grouping
        df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')
        df['DateOnly'] = pd.to_datetime(df['Date']).dt.date
        
        # Detect last transaction per day
        df['is_last_of_day'] = False
        for date in df['DateOnly'].unique():
            last_idx = df[df['DateOnly'] == date].index[-1]
            df.loc[last_idx, 'is_last_of_day'] = True
        
        # Daily balance table - strategy depends on bank type
        daily_balance_data = []
        
        # Check if this is BCA (has backdate transactions with "TANGGAL :")
        has_backdate = df['Description'].str.contains('TANGGAL :', case=False, na=False).any()
        
        if has_backdate:
            # BCA Strategy: Use first non-backdate transaction balance
            for date in sorted(df['DateOnly'].unique()):
                day_transactions = df[df['DateOnly'] == date]
                
                balance_value = '0.00'
                
                # Find FIRST non-backdate Debit with balance
                non_backdate_debit = day_transactions[
                    (day_transactions['Type'] == 'Debit') & 
                    (~day_transactions['Description'].str.contains('TANGGAL :', case=False, na=False)) &
                    (day_transactions['Balance'] != '0.00')
                ]
                
                if len(non_backdate_debit) > 0:
                    balance_value = non_backdate_debit.iloc[0]['Balance']
                else:
                    # Find FIRST non-backdate Credit with balance
                    non_backdate_credit = day_transactions[
                        (day_transactions['Type'] == 'Credit') & 
                        (~day_transactions['Description'].str.contains('TANGGAL :', case=False, na=False)) &
                        (day_transactions['Balance'] != '0.00')
                    ]
                    
                    if len(non_backdate_credit) > 0:
                        balance_value = non_backdate_credit.iloc[0]['Balance']
                    else:
                        # Fallback: Use first balance (any)
                        non_zero = day_transactions[day_transactions['Balance'] != '0.00']
                        if len(non_zero) > 0:
                            balance_value = non_zero.iloc[0]['Balance']
                
                daily_balance_data.append({
                    'Date': day_transactions.iloc[0]['Date'],
                    'Balance': balance_value
                })
        else:
            # Other banks (Bank Kalsel, Mandiri, etc.): Use LAST balance of the day
            for date in sorted(df['DateOnly'].unique()):
                day_transactions = df[df['DateOnly'] == date]
                
                balance_value = '0.00'
                
                # Strategy: Get LAST transaction balance (end of day balance)
                non_zero = day_transactions[day_transactions['Balance'] != '0.00']
                
                if len(non_zero) > 0:
                    # Use LAST balance (final transaction of the day)
                    balance_value = non_zero.iloc[-1]['Balance']
                
                daily_balance_data.append({
                    'Date': day_transactions.iloc[0]['Date'],
                    'Balance': balance_value
                })
        
        # Monthly summary
        monthly_summary = []
        for month in df['Month'].unique():
            month_data = df[df['Month'] == month]
            
            total_debit = month_data[month_data['Type'] == 'Debit']['Amount_numeric'].sum()
            total_credit = month_data[month_data['Type'] == 'Credit']['Amount_numeric'].sum()
            freq_debit = len(month_data[month_data['Type'] == 'Debit'])
            freq_credit = len(month_data[month_data['Type'] == 'Credit'])
            
            # Format for display
            from processors.bsi_processor import format_indonesian_number
            
            monthly_summary.append({
                'month': str(month),
                'monthName': month.strftime('%B %Y'),
                'totalDebit': format_indonesian_number(total_debit),
                'totalCredit': format_indonesian_number(total_credit),
                'freqDebit': freq_debit,
                'freqCredit': freq_credit,
                'totalDebitNumeric': float(total_debit),
                'totalCreditNumeric': float(total_credit)
            })
        
        # All data for display
        all_data = df[['Date', 'Reference', 'Description', 'Type', 'Amount', 'Balance', 'is_last_of_day']].to_dict('records')
        total_records = len(df)
        
        # Check if we have PDF summary (from Mandiri PDF)
        pdf_summary = df.attrs.get('pdf_summary', None)
        account_info = df.attrs.get('account_info', None)
        
        if pdf_summary:
            # Use summary from PDF (more accurate)
            total_debit = pdf_summary['total_amount_debited']
            total_credit = pdf_summary['total_amount_credited']
            balance = total_credit - total_debit
            
            summary = {
                'totalRecords': total_records,
                'totalDebit': float(total_debit),
                'totalCredit': float(total_credit),
                'balance': float(balance),
                'dateRange': {
                    'start': df['Date'].min().strftime('%Y-%m-%d'),
                    'end': df['Date'].max().strftime('%Y-%m-%d')
                },
                'fileType': file_type,
                'summarySource': 'PDF Summary (Accurate)'
            }
        else:
            # Calculate from transactions (fallback)
            total_debit = df[df['Type'] == 'Debit']['Amount_numeric'].sum()
            total_credit = df[df['Type'] == 'Credit']['Amount_numeric'].sum()
            balance = total_credit - total_debit
            
            summary = {
                'totalRecords': total_records,
                'totalDebit': float(total_debit),
                'totalCredit': float(total_credit),
                'balance': float(balance),
                'dateRange': {
                    'start': df['Date'].min().strftime('%Y-%m-%d'),
                    'end': df['Date'].max().strftime('%Y-%m-%d')
                },
                'fileType': file_type,
                'summarySource': 'Calculated from Transactions'
            }
        
        # Save processed data temporarily (without numeric helper columns)
        temp_filename = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
        df_output = df[['Date', 'Reference', 'Description', 'Type', 'Amount', 'Balance']]
        df_output.to_csv(temp_path, index=False)
        
        return jsonify({
            'success': True,
            'allData': all_data,
            'dailyBalance': daily_balance_data,
            'monthlySummary': monthly_summary,
            'summary': summary,
            'tempFile': temp_filename,
            'accountInfo': account_info
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error processing file: {error_detail}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/download/<format>', methods=['POST'])
def download_file(format):
    try:
        data = request.json
        temp_filename = data.get('tempFile')
        mode = data.get('mode', 'full')  # Get mode from request (default: full)
        filters = data.get('filters', {})  # Get filters from request
        
        if not temp_filename:
            return jsonify({'error': 'No temp file provided'}), 400
        
        temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
        
        if not os.path.exists(temp_path):
            return jsonify({'error': 'Temp file not found'}), 404
        
        # Read the processed data
        df = pd.read_csv(temp_path)
        
        # Special handling for IDEB mode
        if mode == 'ideb':
            output_filename = f"ideb_slik_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Read debitur name from first line of temp file
            debitur_name = 'Unknown'
            with open(temp_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if first_line.startswith('# DEBITUR_NAME:'):
                    debitur_name = first_line.replace('# DEBITUR_NAME:', '').strip()
            
            # Read the CSV (skip first line if it's comment)
            df = pd.read_csv(temp_path, comment='#')
            
            # Helper function to parse Indonesian number format (with all commas)
            def parse_indonesian_number(val):
                if pd.isna(val) or val == '' or val == '-':
                    return 0.0
                val_str = str(val).strip()
                
                # Format: 1,250,000,000,00 (all commas)
                last_comma_pos = val_str.rfind(',')
                
                if last_comma_pos == -1:
                    try:
                        return float(val_str)
                    except:
                        return 0.0
                
                # Check if last comma is decimal (within last 3 chars)
                if len(val_str) - last_comma_pos <= 3:
                    before_decimal = val_str[:last_comma_pos].replace(',', '')
                    after_decimal = val_str[last_comma_pos + 1:]
                    val_str = f"{before_decimal}.{after_decimal}"
                else:
                    val_str = val_str.replace(',', '')
                
                try:
                    return float(val_str)
                except:
                    return 0.0
            
            # Calculate totals
            df_numeric = df.copy()
            df_numeric['Plafon_numeric'] = df_numeric['Plafon'].apply(parse_indonesian_number)
            df_numeric['OS_numeric'] = df_numeric['O/S'].apply(parse_indonesian_number)
            df_numeric['Angsuran_numeric'] = df_numeric['Angsuran'].apply(parse_indonesian_number)
            
            total_plafon = df_numeric['Plafon_numeric'].sum()
            total_os = df_numeric['OS_numeric'].sum()
            total_angsuran = df_numeric['Angsuran_numeric'].sum()
            
            if format == 'excel':
                output_path = os.path.join(OUTPUT_FOLDER, f"{output_filename}.xlsx")
                
                # Create Excel with custom formatting
                from openpyxl import Workbook
                from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
                from openpyxl.utils import get_column_letter
                from datetime import datetime as dt
                
                wb = Workbook()
                ws = wb.active
                ws.title = "IDEB SLIK"
                
                # A1: Debitur Name (MATCHING NEW SCREENSHOT)
                ws['A1'] = debitur_name.upper()
                ws['A1'].font = Font(bold=True, size=11)
                
                # Row 2: Table Header (starting from column A) - MATCHING NEW SCREENSHOT
                headers = ['No', 'Nama Bank', 'Plafon', 'Yield (%)', 'O/S', 'Tanggal Pencairan', 'Tanggal Jatuh Tempo', 'Jk Waktu', 'Kol', 'Angsuran', 'Jenis Penggunaan']
                header_row = 2
                start_col = 1  # A column (not B!)
                
                # Define colors based on NEW screenshot
                header_fill = PatternFill(start_color="BFBFBF", end_color="BFBFBF", fill_type="solid")  # Gray for headers
                no_col_fill = PatternFill(start_color="BFBFBF", end_color="BFBFBF", fill_type="solid")  # Gray for No column
                header_font = Font(bold=True, size=10)
                header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                thin_border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
                
                # Write headers
                for col_idx, header in enumerate(headers, start=start_col):
                    cell = ws.cell(row=header_row, column=col_idx)
                    cell.value = header
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
                    cell.border = thin_border
                
                # Write data rows (starting from row 3)
                data_start_row = header_row + 1
                for row_idx, (_, row) in enumerate(df.iterrows(), start=data_start_row):
                    # No (column A) - WITH GRAY BACKGROUND
                    cell_no = ws.cell(row=row_idx, column=start_col, value=row_idx - header_row)
                    cell_no.fill = no_col_fill  # Gray background for No column
                    cell_no.alignment = Alignment(horizontal='center', vertical='center')
                    cell_no.border = thin_border
                    
                    # Nama Bank (column B)
                    cell_bank = ws.cell(row=row_idx, column=start_col + 1, value=row['Nama Bank'])
                    cell_bank.border = thin_border
                    
                    # Plafon (column C) - number format
                    plafon_val = parse_indonesian_number(row['Plafon'])
                    cell_plafon = ws.cell(row=row_idx, column=start_col + 2, value=plafon_val)
                    cell_plafon.number_format = '#,##0'
                    cell_plafon.alignment = Alignment(horizontal='right', vertical='center')
                    cell_plafon.border = thin_border
                    
                    # Yield (column D) - percentage format
                    yield_val = row['Yield (%)']
                    if isinstance(yield_val, str):
                        yield_val = yield_val.replace('%', '').strip()
                    try:
                        yield_float = float(str(yield_val).replace(',', '.'))
                        yield_decimal = yield_float / 100
                        cell_yield = ws.cell(row=row_idx, column=start_col + 3, value=yield_decimal)
                        cell_yield.number_format = '0.00%'
                    except:
                        cell_yield = ws.cell(row=row_idx, column=start_col + 3, value=yield_val)
                    cell_yield.alignment = Alignment(horizontal='center', vertical='center')
                    cell_yield.border = thin_border
                    
                    # O/S (column E) - number format
                    os_val = parse_indonesian_number(row['O/S'])
                    cell_os = ws.cell(row=row_idx, column=start_col + 4, value=os_val)
                    cell_os.number_format = '#,##0'
                    cell_os.alignment = Alignment(horizontal='right', vertical='center')
                    cell_os.border = thin_border
                    
                    # Tanggal Pencairan (column F) - date format
                    date_pencairan_str = row['Tanggal Pencairan']
                    try:
                        date_obj = dt.strptime(date_pencairan_str, '%m/%d/%Y')
                        cell_tgl = ws.cell(row=row_idx, column=start_col + 5, value=date_obj)
                        cell_tgl.number_format = 'DD-MMM-YY'
                    except:
                        cell_tgl = ws.cell(row=row_idx, column=start_col + 5, value=date_pencairan_str)
                    cell_tgl.alignment = Alignment(horizontal='center', vertical='center')
                    cell_tgl.border = thin_border
                    
                    # Tanggal Jatuh Tempo (column G) - date format
                    date_tempo_str = row['Tanggal Jatuh Tempo']
                    try:
                        date_obj = dt.strptime(date_tempo_str, '%m/%d/%Y')
                        cell_tgl2 = ws.cell(row=row_idx, column=start_col + 6, value=date_obj)
                        cell_tgl2.number_format = 'DD-MMM-YY'
                    except:
                        cell_tgl2 = ws.cell(row=row_idx, column=start_col + 6, value=date_tempo_str)
                    cell_tgl2.alignment = Alignment(horizontal='center', vertical='center')
                    cell_tgl2.border = thin_border
                    
                    # Jk Waktu (column H)
                    cell_jk = ws.cell(row=row_idx, column=start_col + 7, value=row['Jk Waktu'])
                    cell_jk.alignment = Alignment(horizontal='center', vertical='center')
                    cell_jk.border = thin_border
                    
                    # Kol (column I)
                    cell_kol = ws.cell(row=row_idx, column=start_col + 8, value=row['Kol'])
                    cell_kol.alignment = Alignment(horizontal='center', vertical='center')
                    cell_kol.border = thin_border
                    
                    # Angsuran (column J) - number format
                    angsuran_val = parse_indonesian_number(row['Angsuran'])
                    cell_angsuran = ws.cell(row=row_idx, column=start_col + 9, value=angsuran_val)
                    cell_angsuran.number_format = '#,##0'
                    cell_angsuran.alignment = Alignment(horizontal='right', vertical='center')
                    cell_angsuran.border = thin_border
                    
                    # Jenis Penggunaan (column K) - NEW!
                    jenis_penggunaan = row.get('Jenis Konsumsi', '')
                    cell_jenis = ws.cell(row=row_idx, column=start_col + 10, value=jenis_penggunaan)
                    cell_jenis.alignment = Alignment(horizontal='center', vertical='center')
                    cell_jenis.border = thin_border
                
                # Total row - MATCHING NEW SCREENSHOT
                total_row = data_start_row + len(df)
                total_fill = PatternFill(start_color="BFBFBF", end_color="BFBFBF", fill_type="solid")  # Gray (matching header)
                total_font = Font(bold=True)
                
                # "Total" label (merge A and B)
                ws.merge_cells(f'A{total_row}:B{total_row}')
                cell_total_label = ws.cell(row=total_row, column=start_col)
                cell_total_label.value = "Total"
                cell_total_label.fill = total_fill
                cell_total_label.font = total_font
                cell_total_label.alignment = Alignment(horizontal='center', vertical='center')
                cell_total_label.border = thin_border
                
                # Total Plafon (column C)
                cell_total_plafon = ws.cell(row=total_row, column=start_col + 2, value=total_plafon)
                cell_total_plafon.number_format = '#,##0'
                cell_total_plafon.fill = total_fill
                cell_total_plafon.font = total_font
                cell_total_plafon.alignment = Alignment(horizontal='right', vertical='center')
                cell_total_plafon.border = thin_border
                
                # Empty cells with gray background (D=Yield, F=Tgl Pencairan, G=Tgl Jatuh Tempo, H=Jk Waktu, I=Kol, K=Jenis Penggunaan)
                for col_offset in [3, 5, 6, 7, 8, 10]:
                    cell = ws.cell(row=total_row, column=start_col + col_offset)
                    cell.fill = total_fill
                    cell.border = thin_border
                
                # Total O/S (column E)
                cell_total_os = ws.cell(row=total_row, column=start_col + 4, value=total_os)
                cell_total_os.number_format = '#,##0'
                cell_total_os.fill = total_fill
                cell_total_os.font = total_font
                cell_total_os.alignment = Alignment(horizontal='right', vertical='center')
                cell_total_os.border = thin_border
                
                # Total Angsuran (column J)
                cell_total_angsuran = ws.cell(row=total_row, column=start_col + 9, value=total_angsuran)
                cell_total_angsuran.number_format = '#,##0'
                cell_total_angsuran.fill = total_fill
                cell_total_angsuran.font = total_font
                cell_total_angsuran.alignment = Alignment(horizontal='right', vertical='center')
                cell_total_angsuran.border = thin_border
                
                # Adjust column widths - MATCHING NEW SCREENSHOT
                ws.column_dimensions['A'].width = 5    # No
                ws.column_dimensions['B'].width = 30   # Nama Bank
                ws.column_dimensions['C'].width = 15   # Plafon
                ws.column_dimensions['D'].width = 10   # Yield
                ws.column_dimensions['E'].width = 15   # O/S
                ws.column_dimensions['F'].width = 18   # Tanggal Pencairan
                ws.column_dimensions['G'].width = 18   # Tanggal Jatuh Tempo
                ws.column_dimensions['H'].width = 10   # Jk Waktu
                ws.column_dimensions['I'].width = 6    # Kol
                ws.column_dimensions['J'].width = 15   # Angsuran
                ws.column_dimensions['K'].width = 18   # Jenis Penggunaan
                
                # Save workbook
                wb.save(output_path)
                return send_file(output_path, as_attachment=True, download_name=f"{output_filename}.xlsx")
            
            elif format == 'csv':
                # For CSV, add Total row to DataFrame
                def format_indonesian_number(value):
                    if pd.isna(value) or value == 0:
                        return "0,00"
                    formatted = f"{value:,.2f}"
                    formatted = formatted.replace('.', ',')
                    return formatted
                
                total_row = pd.DataFrame([{
                    'Nama Bank': 'TOTAL',
                    'Plafon': format_indonesian_number(total_plafon),
                    'Yield (%)': '',
                    'O/S': format_indonesian_number(total_os),
                    'Tanggal Pencairan': '',
                    'Tanggal Jatuh Tempo': '',
                    'Jk Waktu': '',
                    'Kol': '',
                    'Angsuran': format_indonesian_number(total_angsuran),
                    'Jenis Penggunaan': ''  # NEW: include for CSV export
                }])
                
                df_with_total = pd.concat([df, total_row], ignore_index=True)
                
                output_path = os.path.join(OUTPUT_FOLDER, f"{output_filename}.csv")
                # Add debitur name as first line
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Debitur: {debitur_name}\n")
                    df_with_total.to_csv(f, index=False)
                
                return send_file(output_path, as_attachment=True, download_name=f"{output_filename}.csv")
            
            else:
                return jsonify({'error': f'Unsupported format: {format}'}), 400
        
        # Apply filters BEFORE mode-specific processing
        if filters:
            # Convert Date to datetime for filtering
            df['Date_parsed'] = pd.to_datetime(df['Date'])
            
            # Filter by month
            selected_month = filters.get('month')
            if selected_month and selected_month != 'all':
                # Extract year and month from selected_month (format: YYYY-MM)
                year_month = selected_month.split('-')
                if len(year_month) == 2:
                    year = int(year_month[0])
                    month = int(year_month[1])
                    df = df[(df['Date_parsed'].dt.year == year) & (df['Date_parsed'].dt.month == month)]
            
            # Filter by date range
            date_start = filters.get('dateStart')
            if date_start:
                df = df[df['Date_parsed'] >= pd.to_datetime(date_start)]
            
            date_end = filters.get('dateEnd')
            if date_end:
                df = df[df['Date_parsed'] <= pd.to_datetime(date_end)]
            
            # Remove helper column
            df = df.drop(columns=['Date_parsed'])
        
        # If mode is 'daily', filter to only last transaction of each day
        if mode == 'daily':
            # Convert Date to datetime (try multiple formats)
            # First try YYYY-MM-DD format (from CSV)
            df['Date_parsed'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
            
            # If that fails, try DD/MM/YYYY format
            if df['Date_parsed'].isna().all():
                df['Date_parsed'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            
            # If still fails, let pandas infer
            if df['Date_parsed'].isna().all():
                df['Date_parsed'] = pd.to_datetime(df['Date'], errors='coerce')
            
            df['DateOnly'] = df['Date_parsed'].dt.date
            
            # Group by date and get last transaction (last row per day)
            daily_df = df.groupby('DateOnly').agg({
                'Date': 'first',
                'Date_parsed': 'first',
                'Balance': 'last'
            }).reset_index()
            
            # Extract day number only (DD) for Tanggal column
            daily_df['Tanggal'] = daily_df['Date_parsed'].dt.day
            
            # Keep only Tanggal (day number) and Balance columns for export
            df = daily_df[['Tanggal', 'Balance']].copy()
            df.columns = ['Tanggal', 'Saldo']
        
        # Generate output filename with filter info (NO "bank_statement_" prefix)
        mode_label = 'full_scan' if mode == 'full' else 'daily_balance'
        filter_label = ''
        
        if filters:
            selected_month = filters.get('month')
            if selected_month and selected_month != 'all':
                filter_label = f"_{selected_month.replace('-', '_')}"
            elif filters.get('dateStart') or filters.get('dateEnd'):
                filter_label = '_filtered'
        
        output_filename = f"{mode_label}{filter_label}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if format == 'excel':
            output_path = os.path.join(OUTPUT_FOLDER, f"{output_filename}.xlsx")
            
            # Write to Excel with proper formatting
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                sheet_name = 'Saldo Harian' if mode == 'daily' else 'Transactions'
                df.to_excel(writer, index=False, sheet_name=sheet_name)
                
                # Get the worksheet
                worksheet = writer.sheets[sheet_name]
                
                # Add summary rows at the bottom
                last_row = len(df) + 2  # +1 for header, +1 for blank row
                
                # Calculate totals
                if mode == 'daily':
                    # For daily balance mode, calculate statistics
                    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
                    
                    # Parse balance values
                    def parse_amount(val):
                        if pd.isna(val) or val == '' or val == '-':
                            return 0.0
                        val_str = str(val).strip().replace('Rp', '').replace(' ', '').strip()
                        
                        # Handle different formats
                        if ',' in val_str and '.' in val_str:
                            last_comma_pos = val_str.rfind(',')
                            last_dot_pos = val_str.rfind('.')
                            
                            if last_dot_pos > last_comma_pos:
                                # International: 1,234,567.89
                                val_str = val_str.replace(',', '')
                            else:
                                # Indonesian: 1.234.567,89
                                val_str = val_str.replace('.', '').replace(',', '.')
                        elif ',' in val_str:
                            val_str = val_str.replace('.', '').replace(',', '.')
                        elif '.' in val_str:
                            last_dot_pos = val_str.rfind('.')
                            decimal_part_length = len(val_str) - last_dot_pos - 1
                            if decimal_part_length == 2:
                                val_str = val_str[:last_dot_pos].replace('.', '') + '.' + val_str[last_dot_pos+1:]
                            else:
                                val_str = val_str.replace('.', '')
                        
                        try:
                            return float(val_str)
                        except:
                            return 0.0
                    
                    df_numeric = df.copy()
                    df_numeric['Balance_numeric'] = df_numeric['Saldo'].apply(parse_amount)
                    
                    # Calculate statistics
                    total_balance = df_numeric['Balance_numeric'].sum()
                    avg_balance = df_numeric['Balance_numeric'].mean()
                    highest_balance = df_numeric['Balance_numeric'].max()
                    lowest_balance = df_numeric['Balance_numeric'].min()
                    
                    # Add blank row
                    stats_start_row = last_row + 1
                    
                    # Statistics section (like template)
                    worksheet.cell(row=stats_start_row, column=1, value='Total')
                    worksheet.cell(row=stats_start_row, column=2, value=total_balance)
                    worksheet.cell(row=stats_start_row, column=2).number_format = '#,##0.00'
                    
                    worksheet.cell(row=stats_start_row + 1, column=1, value='Rata-rata Pengendapan')
                    worksheet.cell(row=stats_start_row + 1, column=2, value=avg_balance)
                    worksheet.cell(row=stats_start_row + 1, column=2).number_format = '#,##0.00'
                    
                    worksheet.cell(row=stats_start_row + 2, column=1, value='Saldo Rata-rata')
                    worksheet.cell(row=stats_start_row + 2, column=2, value=avg_balance)
                    worksheet.cell(row=stats_start_row + 2, column=2).number_format = '#,##0.00'
                    
                    worksheet.cell(row=stats_start_row + 3, column=1, value='Saldo Tertinggi')
                    worksheet.cell(row=stats_start_row + 3, column=2, value=highest_balance)
                    worksheet.cell(row=stats_start_row + 3, column=2).number_format = '#,##0.00'
                    
                    worksheet.cell(row=stats_start_row + 4, column=1, value='Saldo Terendah')
                    worksheet.cell(row=stats_start_row + 4, column=2, value=lowest_balance)
                    worksheet.cell(row=stats_start_row + 4, column=2).number_format = '#,##0.00'
                    
                    # Calculate mutation statistics from original transaction data
                    # Read the original CSV file to get all transactions
                    original_csv_path = os.path.join(OUTPUT_FOLDER, data.get('tempFile'))
                    df_full = pd.read_csv(original_csv_path)
                    
                    # Calculate debit and credit totals
                    total_debit = 0.0
                    total_credit = 0.0
                    freq_debit = 0
                    freq_credit = 0
                    
                    if 'Type' in df_full.columns and 'Amount' in df_full.columns:
                        for _, row in df_full.iterrows():
                            trans_type = str(row['Type']).strip().lower()
                            amount = parse_amount(row['Amount'])
                            
                            if trans_type in ['debit', 'db', 'debet']:
                                total_debit += amount
                                freq_debit += 1
                            elif trans_type in ['credit', 'cr', 'kredit']:
                                total_credit += amount
                                freq_credit += 1
                    
                    # Add blank row before mutation statistics
                    mutation_start_row = stats_start_row + 6
                    
                    # Mutation statistics table header
                    worksheet.merge_cells(start_row=mutation_start_row, start_column=1, end_row=mutation_start_row, end_column=3)
                    header_cell = worksheet.cell(row=mutation_start_row, column=1)
                    header_cell.value = 'Mutasi Debet'
                    header_cell.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
                    header_cell.font = Font(bold=True)
                    header_cell.alignment = Alignment(horizontal='center')
                    
                    worksheet.merge_cells(start_row=mutation_start_row, start_column=4, end_row=mutation_start_row, end_column=6)
                    header_cell2 = worksheet.cell(row=mutation_start_row, column=4)
                    header_cell2.value = 'Mutasi kredit'
                    header_cell2.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
                    header_cell2.font = Font(bold=True)
                    header_cell2.alignment = Alignment(horizontal='center')
                    
                    # Mutation statistics rows with calculated values
                    mutation_rows = [
                        ('Total Mutasi', total_debit, total_credit),
                        ('Adjusted', '-', '-'),
                        ('Total Frekuensi', freq_debit, freq_credit),
                        ('Adjusted', '-', '-')
                    ]
                    
                    for idx, (label, debit_val, credit_val) in enumerate(mutation_rows, start=1):
                        row_num = mutation_start_row + idx
                        worksheet.cell(row=row_num, column=1, value=label)
                        worksheet.merge_cells(start_row=row_num, start_column=2, end_row=row_num, end_column=3)
                        
                        # Set debit value
                        debit_cell = worksheet.cell(row=row_num, column=2)
                        if isinstance(debit_val, (int, float)):
                            debit_cell.value = debit_val
                            debit_cell.number_format = '#,##0.00'
                        else:
                            debit_cell.value = debit_val
                        
                        worksheet.merge_cells(start_row=row_num, start_column=5, end_row=row_num, end_column=6)
                        
                        # Set credit value
                        credit_cell = worksheet.cell(row=row_num, column=5)
                        if isinstance(credit_val, (int, float)):
                            credit_cell.value = credit_val
                            credit_cell.number_format = '#,##0.00'
                        else:
                            credit_cell.value = credit_val
                        
                        # Add borders
                        thin_border = Border(
                            left=Side(style='thin'),
                            right=Side(style='thin'),
                            top=Side(style='thin'),
                            bottom=Side(style='thin')
                        )
                        for col in range(1, 7):
                            worksheet.cell(row=row_num, column=col).border = thin_border
                    
                    # Add borders to header
                    thin_border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )
                    for col in range(1, 7):
                        worksheet.cell(row=mutation_start_row, column=col).border = thin_border
                        
                else:
                    # For full transactions mode, calculate mutasi debit and kredit
                    # Import format functions
                    from processors.bsi_processor import format_indonesian_number
                    
                    def format_english_number(value):
                        """Format number as English/US format: 1,234,567.89 (comma as thousand separator, dot as decimal)"""
                        if pd.isna(value) or value == 0:
                            return "0.00"
                        
                        formatted = f"{value:,.2f}"
                        return formatted
                    
                    # Calculate numeric totals
                    def parse_amount(val):
                        if pd.isna(val) or val == '' or val == '-':
                            return 0.0
                        val_str = str(val).strip().replace('Rp', '').replace(' ', '').strip()
                        
                        # Handle different formats
                        if ',' in val_str and '.' in val_str:
                            last_comma_pos = val_str.rfind(',')
                            last_dot_pos = val_str.rfind('.')
                            
                            if last_dot_pos > last_comma_pos:
                                # International: 1,234,567.89
                                val_str = val_str.replace(',', '')
                            else:
                                # Indonesian: 1.234.567,89
                                val_str = val_str.replace('.', '').replace(',', '.')
                        elif ',' in val_str:
                            # Only comma
                            last_comma_pos = val_str.rfind(',')
                            decimal_part_length = len(val_str) - last_comma_pos - 1
                            
                            if decimal_part_length == 2:
                                val_str = val_str.replace('.', '').replace(',', '.')
                            else:
                                val_str = val_str.replace(',', '')
                        elif '.' in val_str:
                            # Only dots
                            last_dot_pos = val_str.rfind('.')
                            decimal_part_length = len(val_str) - last_dot_pos - 1
                            
                            if decimal_part_length == 2:
                                # Format: 200.000.000.00
                                val_str = val_str[:last_dot_pos].replace('.', '') + '.' + val_str[last_dot_pos+1:]
                            elif decimal_part_length > 3:
                                pass
                            else:
                                val_str = val_str.replace('.', '')
                        
                        try:
                            return float(val_str)
                        except:
                            return 0.0
                    
                    df_numeric = df.copy()
                    df_numeric['Amount_numeric'] = df_numeric['Amount'].apply(parse_amount)
                    df_numeric['Balance_numeric'] = df_numeric['Balance'].apply(parse_amount)
                    
                    total_debit = df_numeric[df_numeric['Type'] == 'Debit']['Amount_numeric'].sum()
                    total_credit = df_numeric[df_numeric['Type'] == 'Credit']['Amount_numeric'].sum()
                    last_balance = df_numeric['Balance_numeric'].iloc[-1] if len(df_numeric) > 0 else 0.0
                    
                    # Format to International format (comma as thousand separator, dot as decimal)
                    total_debit_formatted = format_english_number(total_debit)
                    total_credit_formatted = format_english_number(total_credit)
                    last_balance_formatted = format_english_number(last_balance)  # Use International format consistently
                    
                    # Write summary
                    worksheet.cell(row=last_row + 1, column=1, value='TOTAL MUTASI DEBIT:')
                    worksheet.cell(row=last_row + 1, column=2, value=total_debit_formatted)
                    
                    worksheet.cell(row=last_row + 2, column=1, value='TOTAL MUTASI KREDIT:')
                    worksheet.cell(row=last_row + 2, column=2, value=total_credit_formatted)
                    
                    worksheet.cell(row=last_row + 3, column=1, value='SALDO TERAKHIR:')
                    worksheet.cell(row=last_row + 3, column=2, value=last_balance_formatted)
                    
                    # Bold the labels
                    from openpyxl.styles import Font
                    worksheet.cell(row=last_row + 1, column=1).font = Font(bold=True)
                    worksheet.cell(row=last_row + 2, column=1).font = Font(bold=True)
                    worksheet.cell(row=last_row + 3, column=1).font = Font(bold=True)
                
                # Format columns
                for idx, col in enumerate(df.columns, 1):
                    # Set column width based on column name
                    col_letter = chr(64 + idx)
                    
                    if mode == 'daily':
                        # Daily balance columns
                        if 'Tanggal' in col or 'Date' in col:
                            worksheet.column_dimensions[col_letter].width = 15
                        elif 'Saldo' in col or 'Balance' in col:
                            worksheet.column_dimensions[col_letter].width = 20
                    else:
                        # Full scan columns
                        if col == 'Date':
                            worksheet.column_dimensions[col_letter].width = 12
                        elif col == 'Reference':
                            worksheet.column_dimensions[col_letter].width = 20
                        elif col == 'Description':
                            worksheet.column_dimensions[col_letter].width = 40
                        elif col == 'Type':
                            worksheet.column_dimensions[col_letter].width = 10
                        elif col in ['Amount', 'Balance']:
                            worksheet.column_dimensions[col_letter].width = 15
            
            return send_file(output_path, as_attachment=True, download_name=f"{output_filename}.xlsx")
        
        elif format == 'csv':
            output_path = os.path.join(OUTPUT_FOLDER, f"{output_filename}.csv")
            # CSV already in Indonesian format from temp file
            df.to_csv(output_path, index=False)
            return send_file(output_path, as_attachment=True, download_name=f"{output_filename}.csv")
        
        elif format == 'pdf':
            # PDF format not implemented yet
            return jsonify({'error': 'PDF download not implemented yet. Use Excel or CSV.'}), 400
        
        else:
            return jsonify({'error': 'Invalid format'}), 400
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error downloading file: {error_detail}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/upload-angsuran', methods=['POST'])
def upload_angsuran():
    """
    Upload and process batch Angsuran files
    Expects multiple Excel files with loan installment schedules
    """
    try:
        # Check if files exist
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if len(files) == 0:
            return jsonify({'error': 'No files selected'}), 400
        
        # Get filter parameters
        filter_month = request.form.get('filterMonth')  # Optional: 1-12
        filter_year = request.form.get('filterYear')    # Optional: e.g. 2026
        
        # Convert to int if provided
        if filter_month and filter_month != 'all':
            filter_month = int(filter_month)
        else:
            filter_month = None
        
        if filter_year and filter_year != 'all':
            filter_year = int(filter_year)
        else:
            filter_year = None
        
        # Save files temporarily
        file_paths = []
        for file in files:
            filename = file.filename
            
            # Validate file extension
            if not filename.lower().endswith(('.xlsx', '.xls')):
                return jsonify({'error': f'Invalid file type for {filename}. Only Excel files (.xlsx, .xls) are supported'}), 400
            
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            file_paths.append(filepath)
        
        # Process batch
        result = process_angsuran_batch(file_paths, filter_month=filter_month, filter_year=filter_year)
        
        # Save summary to CSV (temporary)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        temp_filename = f"angsuran_summary_{timestamp}.csv"
        temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
        
        # Write to CSV with metadata
        with open(temp_path, 'w', encoding='utf-8') as f:
            # Add filter info as comment
            f.write(f"# FILTER_MONTH:{filter_month if filter_month else 'all'}\n")
            f.write(f"# FILTER_YEAR:{filter_year if filter_year else 'all'}\n")
            result['summary'].to_csv(f, index=False)
        
        # Prepare response
        summary_data = result['summary'].to_dict(orient='records')
        
        # Format numbers for display
        for row in summary_data:
            if 'Plafon' in row:
                row['Plafon'] = f"{row['Plafon']:,.2f}"
            if 'Outstanding' in row:
                row['Outstanding'] = f"{row['Outstanding']:,.2f}"
            if 'Porsi Pokok' in row:
                row['Porsi Pokok'] = f"{row['Porsi Pokok']:,.2f}"
            if 'Porsi Margin' in row:
                row['Porsi Margin'] = f"{row['Porsi Margin']:,.2f}"
            if 'Total' in row:
                row['Total'] = f"{row['Total']:,.2f}"
            if 'Periode' in row:
                # Format date
                try:
                    periode_dt = pd.to_datetime(row['Periode'])
                    row['Periode'] = periode_dt.strftime('%Y-%m-%d')
                except:
                    pass
        
        response_data = {
            'mode': 'angsuran',
            'data': summary_data,
            'tempFile': temp_filename,
            'summary': {
                'totalContracts': result['stats']['total_contracts'],
                'totalPlafon': f"{result['stats']['total_plafon']:,.2f}",
                'totalOutstanding': f"{result['stats']['total_outstanding']:,.2f}",
                'totalPorsiPokok': f"{result['stats']['total_porsi_pokok']:,.2f}",
                'totalPorsiMargin': f"{result['stats']['total_porsi_margin']:,.2f}",
                'totalAngsuran': f"{result['stats']['total_angsuran']:,.2f}"
            },
            'errors': result['errors'],
            'filter': {
                'month': filter_month,
                'year': filter_year
            }
        }
        
        return jsonify(response_data), 200
    
    except Exception as e:
        return jsonify({'error': f'Error processing files: {str(e)}'}), 500


@app.route('/api/download-angsuran/<format>', methods=['POST'])
def download_angsuran(format):
    """
    Download Angsuran data in Excel/CSV format
    """
    try:
        data = request.json
        temp_filename = data.get('tempFile')
        
        if not temp_filename:
            return jsonify({'error': 'No temp file provided'}), 400
        
        temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
        
        if not os.path.exists(temp_path):
            return jsonify({'error': 'Temp file not found'}), 404
        
        # Read filter info from temp file
        filter_month = None
        filter_year = None
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if first_line.startswith('# FILTER_MONTH:'):
                filter_month_str = first_line.replace('# FILTER_MONTH:', '').strip()
                filter_month = None if filter_month_str == 'all' else int(filter_month_str)
            
            second_line = f.readline()
            if second_line.startswith('# FILTER_YEAR:'):
                filter_year_str = second_line.replace('# FILTER_YEAR:', '').strip()
                filter_year = None if filter_year_str == 'all' else int(filter_year_str)
        
        # Read summary data (skip comment lines)
        df = pd.read_csv(temp_path, comment='#')
        
        # Helper function to parse Indonesian number format
        def parse_indonesian_number(val):
            if pd.isna(val) or val == '' or val == '-':
                return 0.0
            val_str = str(val).strip()
            val_str = val_str.replace(',', '')
            try:
                return float(val_str)
            except:
                return 0.0
        
        # Calculate stats
        df_numeric = df.copy()
        for col in ['Plafon', 'Outstanding', 'Porsi Pokok', 'Porsi Margin', 'Total']:
            if col in df_numeric.columns:
                df_numeric[f'{col}_numeric'] = df_numeric[col].apply(parse_indonesian_number)
        
        stats = {
            'total_angsuran': df_numeric['Total_numeric'].sum() if 'Total_numeric' in df_numeric.columns else 0,
            'total_porsi_pokok': df_numeric['Porsi Pokok_numeric'].sum() if 'Porsi Pokok_numeric' in df_numeric.columns else 0,
            'total_porsi_margin': df_numeric['Porsi Margin_numeric'].sum() if 'Porsi Margin_numeric' in df_numeric.columns else 0
        }
        
        # Generate filename - use "angsuran_kop" prefix
        month_str = f"{filter_month:02d}" if filter_month else 'all'
        year_str = str(filter_year) if filter_year else 'all'
        output_filename = f"angsuran_kop_{month_str}_{year_str}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if format == 'excel':
            output_path = os.path.join(OUTPUT_FOLDER, f"{output_filename}.xlsx")
            
            # Export with formatting
            sheet_name = f"Angsuran {month_str}-{year_str}"
            export_to_excel_angsuran(df, stats, output_path, sheet_name=sheet_name)
            
            return send_file(output_path, as_attachment=True, download_name=f"{output_filename}.xlsx")
        
        elif format == 'csv':
            output_path = os.path.join(OUTPUT_FOLDER, f"{output_filename}.csv")
            df.to_csv(output_path, index=False)
            
            return send_file(output_path, as_attachment=True, download_name=f"{output_filename}.csv")
        
        else:
            return jsonify({'error': f'Unsupported format: {format}'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


