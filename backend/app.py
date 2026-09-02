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
from processors.ideb_processor import process_ideb_file

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
            last_comma_pos = value.rfind(',')
            if last_comma_pos == -1:
                return float(value)
            if len(value) - last_comma_pos <= 3:
                before_decimal = value[:last_comma_pos].replace(',', '')
                after_decimal = value[last_comma_pos+1:]
                return float(f"{before_decimal}.{after_decimal}")
            else:
                return float(value.replace(',', ''))
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
    
    # Daily balance table
    daily_balance = df[df['is_last_of_day']][['Date', 'Balance']].copy()
    daily_balance_data = daily_balance.to_dict('records')
    
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
            Indonesian format: 1,234,567,89 where comma is BOTH thousand separator AND decimal separator
            The LAST comma is the decimal separator, others are thousand separators
            """
            if isinstance(value, str):
                # Remove thousand separators (all commas except the last one)
                # Then convert last comma to dot for decimal
                
                # Find position of last comma
                last_comma_pos = value.rfind(',')
                
                if last_comma_pos == -1:
                    # No comma, just parse as is
                    return float(value)
                
                # Check if last comma is in last 3 positions (decimal separator)
                if len(value) - last_comma_pos <= 3:
                    # Last comma is decimal separator
                    # Remove all commas except the last one, then replace last comma with dot
                    before_decimal = value[:last_comma_pos].replace(',', '')
                    after_decimal = value[last_comma_pos+1:]
                    return float(f"{before_decimal}.{after_decimal}")
                else:
                    # All commas are thousand separators
                    return float(value.replace(',', ''))
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
        
        # Daily balance table (one row per day)
        daily_balance = df[df['is_last_of_day']][['Date', 'Balance']].copy()
        daily_balance_data = daily_balance.to_dict('records')
        
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
                
                # B4: Debitur Name
                ws['B4'] = debitur_name.upper()
                ws['B4'].font = Font(bold=True, size=12)
                
                # B5: Table Header (Row 5, starting from column B)
                headers = ['No', 'Nama Bank', 'Plafon', 'Yield (%)', 'O/S', 'Tanggal Pencairan', 'Tanggal Jatuh Tempo', 'Jk Waktu', 'Kol', 'Angsuran']
                header_row = 5
                start_col = 2  # B column
                
                # Define colors based on screenshot
                header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")  # Light gray
                header_font = Font(bold=True, size=10)
                header_alignment = Alignment(horizontal='center', vertical='center')
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
                
                # Write data rows
                data_start_row = header_row + 1
                for row_idx, (_, row) in enumerate(df.iterrows(), start=data_start_row):
                    # No (column B)
                    ws.cell(row=row_idx, column=start_col, value=row_idx - header_row)
                    
                    # Nama Bank (column C)
                    ws.cell(row=row_idx, column=start_col + 1, value=row['Nama Bank'])
                    
                    # Plafon (column D) - number format
                    plafon_val = parse_indonesian_number(row['Plafon'])
                    cell_plafon = ws.cell(row=row_idx, column=start_col + 2, value=plafon_val)
                    cell_plafon.number_format = '#,##0'
                    
                    # Yield (column E) - display as number not percentage (3.5 not 3.5%)
                    yield_val = row['Yield (%)']
                    # Remove % if exists
                    if isinstance(yield_val, str):
                        yield_val = yield_val.replace('%', '').strip()
                    try:
                        yield_float = float(str(yield_val).replace(',', '.'))
                        cell_yield = ws.cell(row=row_idx, column=start_col + 3, value=yield_float)
                        cell_yield.number_format = '0.00'  # Display as 3.50 not 3.50%
                    except:
                        ws.cell(row=row_idx, column=start_col + 3, value=yield_val)
                    
                    # O/S (column F) - number format
                    os_val = parse_indonesian_number(row['O/S'])
                    cell_os = ws.cell(row=row_idx, column=start_col + 4, value=os_val)
                    cell_os.number_format = '#,##0'
                    
                    # Tanggal Pencairan (column G) - date format: 16-Dec-21
                    date_pencairan_str = row['Tanggal Pencairan']
                    try:
                        # Parse mm/dd/yyyy format
                        date_obj = dt.strptime(date_pencairan_str, '%m/%d/%Y')
                        cell_tgl = ws.cell(row=row_idx, column=start_col + 5, value=date_obj)
                        cell_tgl.number_format = 'DD-MMM-YY'
                    except:
                        ws.cell(row=row_idx, column=start_col + 5, value=date_pencairan_str)
                    
                    # Tanggal Jatuh Tempo (column H) - date format: 16-Dec-21
                    date_tempo_str = row['Tanggal Jatuh Tempo']
                    try:
                        date_obj = dt.strptime(date_tempo_str, '%m/%d/%Y')
                        cell_tgl2 = ws.cell(row=row_idx, column=start_col + 6, value=date_obj)
                        cell_tgl2.number_format = 'DD-MMM-YY'
                    except:
                        ws.cell(row=row_idx, column=start_col + 6, value=date_tempo_str)
                    
                    # Jk Waktu (column I)
                    ws.cell(row=row_idx, column=start_col + 7, value=row['Jk Waktu'])
                    
                    # Kol (column J)
                    ws.cell(row=row_idx, column=start_col + 8, value=row['Kol'])
                    
                    # Angsuran (column K) - number format
                    angsuran_val = parse_indonesian_number(row['Angsuran'])
                    cell_angsuran = ws.cell(row=row_idx, column=start_col + 9, value=angsuran_val)
                    cell_angsuran.number_format = '#,##0'
                    
                    # Apply borders to all cells in this row
                    for col_idx in range(start_col, start_col + 10):
                        ws.cell(row=row_idx, column=col_idx).border = thin_border
                
                # Total row
                total_row = data_start_row + len(df)
                total_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")  # Yellow
                total_font = Font(bold=True)
                
                # "Total" label (merge B and C)
                ws.merge_cells(f'B{total_row}:C{total_row}')
                cell_total_label = ws.cell(row=total_row, column=start_col)
                cell_total_label.value = "Total"
                cell_total_label.fill = total_fill
                cell_total_label.font = total_font
                cell_total_label.alignment = Alignment(horizontal='center', vertical='center')
                cell_total_label.border = thin_border
                
                # Total Plafon (column D)
                cell_total_plafon = ws.cell(row=total_row, column=start_col + 2, value=total_plafon)
                cell_total_plafon.number_format = '#,##0'
                cell_total_plafon.fill = total_fill
                cell_total_plafon.font = total_font
                cell_total_plafon.border = thin_border
                
                # Empty cells with yellow background (E, F, G, H, I, J)
                for col_offset in [3, 4, 5, 6, 7, 8]:
                    cell = ws.cell(row=total_row, column=start_col + col_offset)
                    cell.fill = total_fill
                    cell.border = thin_border
                
                # Total O/S (but left empty per screenshot - only Plafon and Angsuran have totals)
                # Actually from screenshot, O/S also has total
                cell_total_os = ws.cell(row=total_row, column=start_col + 4, value=total_os)
                cell_total_os.number_format = '#,##0'
                cell_total_os.fill = total_fill
                cell_total_os.font = total_font
                cell_total_os.border = thin_border
                
                # Total Angsuran (column K)
                cell_total_angsuran = ws.cell(row=total_row, column=start_col + 9, value=total_angsuran)
                cell_total_angsuran.number_format = '#,##0'
                cell_total_angsuran.fill = total_fill
                cell_total_angsuran.font = total_font
                cell_total_angsuran.border = thin_border
                
                # Adjust column widths
                ws.column_dimensions['A'].width = 2
                ws.column_dimensions['B'].width = 6
                ws.column_dimensions['C'].width = 30
                ws.column_dimensions['D'].width = 15
                ws.column_dimensions['E'].width = 10
                ws.column_dimensions['F'].width = 15
                ws.column_dimensions['G'].width = 12
                ws.column_dimensions['H'].width = 12
                ws.column_dimensions['I'].width = 10
                ws.column_dimensions['J'].width = 6
                ws.column_dimensions['K'].width = 15
                
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
                    'Jenis Konsumsi': '',
                    'Angsuran': format_indonesian_number(total_angsuran)
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
            # Convert Date to datetime
            df['Date_parsed'] = pd.to_datetime(df['Date'])
            df['DateOnly'] = df['Date_parsed'].dt.date
            
            # Group by date and get last transaction (last row per day)
            daily_df = df.groupby('DateOnly').last().reset_index()
            
            # Keep only Date and Balance columns for daily balance view
            df = daily_df[['Date', 'Balance']].copy()
            df.columns = ['Tanggal', 'Saldo Akhir Hari']
        
        # Generate output filename with filter info
        mode_label = 'full_scan' if mode == 'full' else 'daily_balance'
        filter_label = ''
        
        if filters:
            selected_month = filters.get('month')
            if selected_month and selected_month != 'all':
                filter_label = f"_{selected_month.replace('-', '_')}"
            elif filters.get('dateStart') or filters.get('dateEnd'):
                filter_label = '_filtered'
        
        output_filename = f"bank_statement_{mode_label}{filter_label}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
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
                    # For daily balance mode, show last balance
                    if 'Saldo Akhir' in df.columns:
                        last_balance = df['Saldo Akhir'].iloc[-1] if len(df) > 0 else '0,00'
                        worksheet.cell(row=last_row + 1, column=1, value='SALDO TERAKHIR:')
                        worksheet.cell(row=last_row + 1, column=2, value=last_balance)
                        # Bold the label
                        from openpyxl.styles import Font
                        worksheet.cell(row=last_row + 1, column=1).font = Font(bold=True)
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
                        val_str = str(val).replace('.', '').replace(',', '.')
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
                    
                    # Format to English format (comma as thousand separator, dot as decimal)
                    total_debit_formatted = format_english_number(total_debit)
                    total_credit_formatted = format_english_number(total_credit)
                    last_balance_formatted = format_indonesian_number(last_balance)  # Keep Indonesian for balance to match column
                    
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
