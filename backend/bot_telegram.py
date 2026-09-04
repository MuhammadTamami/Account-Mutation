# -*- coding: utf-8 -*-
"""
Telegram Bot untuk BSI Excel Convert (MURENA)
Mengintegrasikan fungsi processing tanpa mengubah kode aplikasi existing
"""
import os
import sys
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import pandas as pd

# Import processors dari aplikasi existing
from processors.bank_detector import detect_bank
from processors.bsi_processor import process_bsi_file
from processors.mandiri_processor import process_mandiri_file
from processors.mandiri_rk_processor import process_mandiri_rk_file
from processors.bca_processor import process_bca_file
from processors.bri_processor import process_bri_file
from processors.bni_processor import process_bni_file
from processors.bank_kalsel_processor import process_bank_kalsel_file
from processors.byond_processor import process_byond_file
from processors.ideb_processor import process_ideb_file

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "8624088276:AAFPA_9HtGC5hBsD8enfFlNapB7tAYFRDJ8"
AUTHORIZED_USER_ID = 1819390132
TEMP_FOLDER = "bot_temp"
OUTPUT_FOLDER = "outputs"

# Ensure folders exist
os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# User session storage
user_sessions = {}


def is_authorized(user_id: int) -> bool:
    """Check if user is authorized"""
    return user_id == AUTHORIZED_USER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /start command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if not is_authorized(user_id):
        await update.message.reply_text(
            "❌ Maaf, Anda tidak memiliki akses ke bot ini.\n"
            f"User ID Anda: {user_id}"
        )
        return
    
    welcome_message = f"""
🎉 Selamat datang di *MURENA Bot*, {user_name}!

📊 *Analisis Mutasi Rekening via Telegram*

*Fitur yang tersedia:*
/mutasi - Upload mutasi rekening lengkap
/saldo - Upload untuk cek saldo harian
/ideb - Upload IDEB SLIK PDF
/export - Export hasil terakhir (Excel/CSV)
/restart - Restart bot (load fitur terbaru)
/help - Lihat panduan lengkap

*Bank yang didukung:*
✅ BSI • Mandiri • BCA • BRI • BNI • Bank Kalsel • Byond

*Format file:*
📄 PDF • CSV • Excel • Image (OCR)

Kirim file untuk memulai!
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /help command"""
    if not is_authorized(update.effective_user.id):
        return
    
    help_text = """
📖 *PANDUAN PENGGUNAAN MURENA BOT*

*1️⃣ Upload File Mutasi Rekening*
Gunakan: /mutasi
Lalu kirim file PDF/CSV/Excel/Image
Bot akan menganalisis dan mengirim hasil

*2️⃣ Cek Saldo Harian*
Gunakan: /saldo
Kirim file yang sama
Bot akan extract saldo penutupan per hari

*3️⃣ Analisis IDEB SLIK*
Gunakan: /ideb
Kirim PDF IDEB SLIK
Bot akan extract data kredit (Baki Debet > 0)

*4️⃣ Export Hasil*
Gunakan: /export
Pilih format (Excel/CSV)
Bot akan kirim file hasil terakhir

*5️⃣ Restart Bot*
Gunakan: /restart
Restart bot untuk load fitur terbaru
Berguna setelah ada update kode

*💡 Tips:*
• File maksimal 20MB
• PDF dengan password: kirim file lalu ketik password
• Multi-file: kirim satu per satu

*🔒 Keamanan:*
• File dihapus otomatis setelah diproses
• Hanya Anda yang bisa akses bot ini
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def mutasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /mutasi command"""
    if not is_authorized(update.effective_user.id):
        return
    
    user_id = update.effective_user.id
    user_sessions[user_id] = {'mode': 'full', 'waiting_file': True}
    
    await update.message.reply_text(
        "📊 *Mode: Full Scan Mutasi*\n\n"
        "Silakan kirim file mutasi rekening Anda:\n"
        "• PDF (text atau scanned)\n"
        "• CSV\n"
        "• Excel (XLS/XLSX)\n"
        "• Image (JPG/PNG)\n\n"
        "⏳ Menunggu file...",
        parse_mode='Markdown'
    )


async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /saldo command"""
    if not is_authorized(update.effective_user.id):
        return
    
    user_id = update.effective_user.id
    user_sessions[user_id] = {'mode': 'daily', 'waiting_file': True}
    
    await update.message.reply_text(
        "📅 *Mode: Saldo Harian*\n\n"
        "Silakan kirim file mutasi rekening Anda:\n"
        "Semua format file didukung\n\n"
        "⏳ Menunggu file...",
        parse_mode='Markdown'
    )


async def ideb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /ideb command"""
    if not is_authorized(update.effective_user.id):
        return
    
    user_id = update.effective_user.id
    user_sessions[user_id] = {'mode': 'ideb', 'waiting_file': True}
    
    await update.message.reply_text(
        "📋 *Mode: IDEB SLIK Analyzer*\n\n"
        "Silakan kirim PDF IDEB SLIK Anda\n"
        "Bot akan extract data kredit dengan Baki Debet > 0\n\n"
        "⏳ Menunggu file...",
        parse_mode='Markdown'
    )


async def export_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /export command"""
    if not is_authorized(update.effective_user.id):
        return
    
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or 'last_result' not in session:
        await update.message.reply_text(
            "❌ Tidak ada hasil yang bisa di-export.\n"
            "Silakan proses file terlebih dahulu."
        )
        return
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Excel", callback_data='export_excel'),
            InlineKeyboardButton("📄 CSV", callback_data='export_csv')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📤 *Export Hasil*\n\n"
        "Pilih format export:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /restart command - Restart bot untuk load update terbaru"""
    if not is_authorized(update.effective_user.id):
        return
    
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "🔄 *Restarting Bot...*\n\n"
        "Bot akan restart dalam 2 detik.\n"
        "Fitur terbaru akan di-load otomatis.\n\n"
        "Tunggu sebentar...",
        parse_mode='Markdown'
    )
    
    # Give time for message to be sent
    import asyncio
    await asyncio.sleep(2)
    
    # Restart the bot process
    import os
    import sys
    
    logger.info("Bot restart requested by user")
    
    # Create restart marker file before restarting
    restart_marker = os.path.join(TEMP_FOLDER, '.restart_marker')
    try:
        with open(restart_marker, 'w') as f:
            f.write(str(user_id))
        logger.info(f"Created restart marker: {restart_marker}")
    except Exception as e:
        logger.error(f"Failed to create restart marker: {e}")
    
    # For Windows
    if sys.platform.startswith('win'):
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        # For Linux/Mac
        os.execv(sys.executable, [sys.executable] + sys.argv)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk file yang dikirim user"""
    if not is_authorized(update.effective_user.id):
        return
    
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    
    if not session.get('waiting_file'):
        await update.message.reply_text(
            "❓ Silakan pilih mode terlebih dahulu:\n"
            "/mutasi - Full scan\n"
            "/saldo - Saldo harian\n"
            "/ideb - IDEB SLIK"
        )
        return
    
    # Get file
    document = update.message.document
    if not document:
        await update.message.reply_text("❌ Tidak ada file yang terdeteksi.")
        return
    
    file_name = document.file_name
    file_size = document.file_size
    
    # Check file size (20MB limit)
    if file_size > 20 * 1024 * 1024:
        await update.message.reply_text(
            f"❌ File terlalu besar: {file_size / 1024 / 1024:.1f}MB\n"
            "Maksimal: 20MB"
        )
        return
    
    # Get file extension
    file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
    
    # Validate file type
    valid_extensions = ['pdf', 'csv', 'xlsx', 'xls', 'jpg', 'jpeg', 'png']
    if file_ext not in valid_extensions:
        await update.message.reply_text(
            f"❌ Format file tidak didukung: .{file_ext}\n"
            f"Format yang didukung: {', '.join(valid_extensions)}"
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"⏳ Memproses {file_name}...\n"
        f"Ukuran: {file_size / 1024:.1f}KB"
    )
    
    try:
        # Download file
        file = await context.bot.get_file(document.file_id)
        temp_path = os.path.join(TEMP_FOLDER, f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}")
        await file.download_to_drive(temp_path)
        
        # Process based on mode
        mode = session.get('mode', 'full')
        
        if mode == 'ideb':
            result = await process_ideb_file_bot(temp_path, file_ext, update, processing_msg)
        else:
            result = await process_bank_file_bot(temp_path, file_ext, mode, update, processing_msg)
        
        # Store result in session
        if result:
            user_sessions[user_id]['last_result'] = result
            user_sessions[user_id]['waiting_file'] = False
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"❌ Error memproses file:\n{str(e)}\n\n"
            "Coba lagi atau hubungi admin."
        )


async def process_bank_file_bot(filepath, file_ext, mode, update, processing_msg):
    """Process bank statement file"""
    try:
        # Detect bank
        await processing_msg.edit_text("🔍 Mendeteksi bank...")
        bank_name = detect_bank(filepath, file_ext)
        
        if bank_name == 'UNKNOWN':
            await processing_msg.edit_text(
                "❌ Tidak dapat mendeteksi format bank.\n"
                "Pastikan file Anda adalah mutasi rekening yang valid."
            )
            return None
        
        # Process based on bank
        await processing_msg.edit_text(f"🏦 Bank terdeteksi: {bank_name}\n⏳ Memproses data...")
        
        processor_map = {
            'BSI': process_bsi_file,
            'MANDIRI': process_mandiri_file,
            'MANDIRI_RK': process_mandiri_rk_file,
            'BCA': process_bca_file,
            'BRI': process_bri_file,
            'BNI': process_bni_file,
            'BANK_KALSEL': process_bank_kalsel_file,
            'BYOND': process_byond_file
        }
        
        processor = processor_map.get(bank_name)
        if not processor:
            await processing_msg.edit_text(f"❌ Processor untuk {bank_name} belum tersedia.")
            return None
        
        # Process file
        df = processor(filepath, file_ext)
        
        if df is None or len(df) == 0:
            await processing_msg.edit_text("❌ Tidak ada data yang ditemukan dalam file.")
            return None
        
        # Format result based on mode
        if mode == 'daily':
            result_text = format_daily_balance_result(df, bank_name)
        else:
            result_text = format_full_scan_result(df, bank_name)
        
        await processing_msg.edit_text(result_text, parse_mode='Markdown')
        
        return {
            'df': df,
            'bank_name': bank_name,
            'mode': mode,
            'filepath': filepath
        }
        
    except Exception as e:
        logger.error(f"Error in process_bank_file_bot: {e}", exc_info=True)
        await processing_msg.edit_text(f"❌ Error: {str(e)}")
        return None


async def process_ideb_file_bot(filepath, file_ext, update, processing_msg):
    """Process IDEB SLIK file"""
    try:
        await processing_msg.edit_text("📋 Memproses IDEB SLIK PDF...")
        
        df = process_ideb_file(filepath, file_ext)
        
        if df is None or len(df) == 0:
            await processing_msg.edit_text(
                "❌ Tidak ada data kredit dengan Baki Debet > 0"
            )
            return None
        
        # Get debitur name
        debitur_name = df.attrs.get('debitur_name', 'Unknown')
        
        # Format result
        result_text = format_ideb_result(df, debitur_name)
        
        await processing_msg.edit_text(result_text, parse_mode='Markdown')
        
        return {
            'df': df,
            'debitur_name': debitur_name,
            'mode': 'ideb',
            'filepath': filepath
        }
        
    except Exception as e:
        logger.error(f"Error in process_ideb_file_bot: {e}", exc_info=True)
        await processing_msg.edit_text(f"❌ Error: {str(e)}")
        return None


def format_full_scan_result(df, bank_name):
    """Format full scan result for Telegram"""
    total_records = len(df)
    
    # Parse amounts
    def parse_amount(val):
        if pd.isna(val) or val == '' or val == '-':
            return 0.0
        val_str = str(val).strip()
        
        # Remove "Rp" if present
        val_str = val_str.replace('Rp', '').replace(' ', '').strip()
        
        # Find last separator
        last_comma = val_str.rfind(',')
        last_dot = val_str.rfind('.')
        
        if last_comma > last_dot:
            # Format: 1.234.567,89 (Indonesian)
            val_str = val_str.replace('.', '').replace(',', '.')
        elif last_dot > last_comma:
            # Format: 1,234,567.89 (International)
            val_str = val_str.replace(',', '')
        
        try:
            return float(val_str)
        except:
            return 0.0
    
    # Format number as: 195,000,000.00
    def format_number(val):
        if pd.isna(val) or val == 0:
            return "0.00"
        return f"{val:,.2f}"
    
    df['Amount_numeric'] = df['Amount'].apply(parse_amount)
    
    # FIX: If Amount is empty/'-', calculate from balance difference
    if 'Balance' in df.columns and df['Amount_numeric'].sum() == 0:
        logger.info("⚠️ Amount column is empty in full scan, calculating from balance difference...")
        df['Balance_numeric'] = df['Balance'].apply(parse_amount)
        df['Amount_calculated'] = 0.0
        
        for i in range(1, len(df)):
            prev_balance = df.loc[i-1, 'Balance_numeric']
            curr_balance = df.loc[i, 'Balance_numeric']
            diff = curr_balance - prev_balance
            
            # Absolute value of difference is the amount
            df.loc[i, 'Amount_calculated'] = abs(diff)
        
        # Use calculated amount
        df['Amount_numeric'] = df['Amount_calculated']
        logger.info(f"✅ Calculated amounts - Total: {df['Amount_numeric'].sum():,.2f}")
    
    total_debit = df[df['Type'] == 'Debit']['Amount_numeric'].sum()
    total_credit = df[df['Type'] == 'Credit']['Amount_numeric'].sum()
    
    freq_debit = len(df[df['Type'] == 'Debit'])
    freq_credit = len(df[df['Type'] == 'Credit'])
    
    date_start = df['Date'].min() if 'Date' in df.columns else 'N/A'
    date_end = df['Date'].max() if 'Date' in df.columns else 'N/A'
    
    result = f"""
✅ *HASIL PROCESSING*

🏦 *Bank:* {bank_name}
📊 *Mode:* Full Scan

📅 *Periode:*
• Dari: {date_start}
• Sampai: {date_end}
• Total Transaksi: {total_records:,}

📈 *Mutasi:*
• Total Debit: Rp {format_number(total_debit)} ({freq_debit}x)
• Total Credit: Rp {format_number(total_credit)} ({freq_credit}x)
• Net: Rp {format_number(total_credit - total_debit)}

💾 Gunakan /export untuk download hasil (Excel/CSV)
"""
    
    return result


def format_daily_balance_result(df, bank_name):
    """Format daily balance result for Telegram - Complete summary with daily balance list"""
    # Parse amounts - handle Indonesian format (koma for both thousand and decimal)
    def parse_amount(val):
        if pd.isna(val) or val == '' or val == '-':
            return 0.0
        val_str = str(val).strip()
        
        # Remove "Rp" if present
        val_str = val_str.replace('Rp', '').replace(' ', '').strip()
        
        # Indonesian format: could be 1.234.567,89 or 1,234,567.89
        # Find last separator (either comma or dot)
        last_comma = val_str.rfind(',')
        last_dot = val_str.rfind('.')
        
        if last_comma > last_dot:
            # Format: 1.234.567,89 (Indonesian)
            # Remove dots, replace comma with dot
            val_str = val_str.replace('.', '').replace(',', '.')
        elif last_dot > last_comma:
            # Format: 1,234,567.89 (International)
            # Remove commas
            val_str = val_str.replace(',', '')
        
        try:
            return float(val_str)
        except:
            return 0.0
    
    # Format number as: 195,000,000.00 (comma for thousand, dot for decimal)
    def format_number(val):
        if pd.isna(val) or val == 0:
            return "0.00"
        return f"{val:,.2f}"
    
    df['Amount_numeric'] = df['Amount'].apply(parse_amount)
    df['Balance_numeric'] = df['Balance'].apply(parse_amount)
    
    # FIX: If Amount is empty/'-', calculate from balance difference
    if df['Amount_numeric'].sum() == 0:
        logger.info("⚠️ Amount column is empty, calculating from balance difference...")
        df['Amount_calculated'] = 0.0
        
        for i in range(1, len(df)):
            prev_balance = df.loc[i-1, 'Balance_numeric']
            curr_balance = df.loc[i, 'Balance_numeric']
            diff = curr_balance - prev_balance
            
            # Absolute value of difference is the amount
            df.loc[i, 'Amount_calculated'] = abs(diff)
        
        # Use calculated amount
        df['Amount_numeric'] = df['Amount_calculated']
        logger.info(f"✅ Calculated amounts - Total: {df['Amount_numeric'].sum():,.2f}")
    
    # Get daily balance (last transaction per day)
    df['Date_parsed'] = pd.to_datetime(df['Date'])
    df['DateOnly'] = df['Date_parsed'].dt.date
    daily_df = df.groupby('DateOnly').agg({
        'Balance_numeric': 'last',
        'Date': 'last'
    }).reset_index()
    daily_df = daily_df.sort_values('DateOnly')
    
    total_days = len(daily_df)
    first_balance = daily_df['Balance_numeric'].iloc[0] if len(daily_df) > 0 else 0
    last_balance = daily_df['Balance_numeric'].iloc[-1] if len(daily_df) > 0 else 0
    
    # Calculate total debit and credit
    total_debit = df[df['Type'] == 'Debit']['Amount_numeric'].sum()
    total_credit = df[df['Type'] == 'Credit']['Amount_numeric'].sum()
    
    # Calculate frequency
    freq_debit = len(df[df['Type'] == 'Debit'])
    freq_credit = len(df[df['Type'] == 'Credit'])
    
    # Date range
    date_start = df['Date'].min() if len(df) > 0 else 'N/A'
    date_end = df['Date'].max() if len(df) > 0 else 'N/A'
    
    result = f"""
✅ *HASIL PROCESSING*

🏦 *Bank:* {bank_name}
📅 *Mode:* Ringkasan Saldo

📊 *Periode:*
• Dari: {date_start}
• Sampai: {date_end}
• Total Hari: {total_days}

💰 *Saldo:*
• Saldo Awal: Rp {format_number(first_balance)}
• Saldo Akhir: Rp {format_number(last_balance)}

📈 *Mutasi:*
• Total Debit: Rp {format_number(total_debit)} ({freq_debit}x)
• Total Credit: Rp {format_number(total_credit)} ({freq_credit}x)
• Net: Rp {format_number(total_credit - total_debit)}

💵 *Detail Saldo per Hari:*
"""
    
    # Show all daily balances
    for _, row in daily_df.iterrows():
        date_str = row['DateOnly'].strftime('%Y-%m-%d')
        balance_str = format_number(row['Balance_numeric'])
        result += f"• {date_str}: Rp {balance_str}\n"
    
    result += "\n💾 Gunakan /export untuk download detail lengkap"
    
    return result


def format_ideb_result(df, debitur_name):
    """Format IDEB result for Telegram - Simple format with max 7 credits shown"""
    total_records = len(df)
    
    # Parse amounts
    def parse_amount(val):
        if pd.isna(val) or val == '' or val == '-':
            return 0.0
        val_str = str(val)
        last_comma_pos = val_str.rfind(',')
        if last_comma_pos != -1 and len(val_str) - last_comma_pos <= 3:
            before_decimal = val_str[:last_comma_pos].replace(',', '')
            after_decimal = val_str[last_comma_pos + 1:]
            val_str = f"{before_decimal}.{after_decimal}"
        else:
            val_str = val_str.replace(',', '')
        try:
            return float(val_str)
        except:
            return 0.0
    
    # Calculate totals from ALL records
    total_plafon = df['Plafon'].apply(parse_amount).sum()
    total_os = df['O/S'].apply(parse_amount).sum()
    total_angsuran = df['Angsuran'].apply(parse_amount).sum()
    
    # Header with summary
    result = f"""📊 *Ringkasan:*
• Total Kredit: {total_records}
• Total Plafon: Rp {total_plafon:,.0f}
• Total O/S: Rp {total_os:,.0f}
• Total Angsuran: Rp {total_angsuran:,.0f}

📋 *Detail Kredit:*

"""
    
    # Show max 7 credits
    MAX_DISPLAY = 7
    display_count = min(total_records, MAX_DISPLAY)
    
    for idx in range(display_count):
        row = df.iloc[idx]
        result += f"{idx + 1}. *{row['Nama Bank']}*\n"
        result += f"   Plafon: {row['Plafon']}\n"
        result += f"   O/S: {row['O/S']}\n"
        result += f"   Angsuran: {row['Angsuran']}\n"
        result += f"   Tgl Pencairan: {row['Tanggal Pencairan']}\n"
        result += f"   Tgl Jatuh Tempo: {row['Tanggal Jatuh Tempo']}\n"
        result += f"   Jangka Waktu: {row['Jk Waktu']} bulan\n"
        result += f"   Kol: {row['Kol']}\n\n"
    
    # If more than 7, show "..."
    if total_records > MAX_DISPLAY:
        result += f"... _dan {total_records - MAX_DISPLAY} kredit lainnya_\n\n"
    
    result += "💾 Gunakan /export untuk download lengkap"
    
    return result


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk callback query (button clicks)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_authorized(user_id):
        return
    
    session = user_sessions.get(user_id)
    if not session or 'last_result' not in session:
        await query.edit_message_text("❌ Tidak ada data untuk di-export.")
        return
    
    result = session['last_result']
    df = result['df']
    mode = result.get('mode', 'full')
    
    try:
        if query.data == 'export_excel':
            await query.edit_message_text("📊 Membuat file Excel...")
            file_path = export_to_excel(df, mode, result, user_id)
            
            await context.bot.send_document(
                chat_id=user_id,
                document=open(file_path, 'rb'),
                filename=os.path.basename(file_path),
                caption="✅ Export Excel selesai!"
            )
            
            # Clean up
            try:
                os.remove(file_path)
            except:
                pass
                
        elif query.data == 'export_csv':
            await query.edit_message_text("📄 Membuat file CSV...")
            file_path = export_to_csv(df, mode, result, user_id)
            
            await context.bot.send_document(
                chat_id=user_id,
                document=open(file_path, 'rb'),
                filename=os.path.basename(file_path),
                caption="✅ Export CSV selesai!"
            )
            
            # Clean up
            try:
                os.remove(file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error in export: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Error export: {str(e)}")


def export_to_excel(df, mode, result, user_id):
    """Export DataFrame to Excel with professional formatting"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    if mode == 'ideb':
        filename = f"ideb_slik_{user_id}_{timestamp}.xlsx"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Export to Excel
        df.to_excel(file_path, index=False, sheet_name='Data Kredit')
        
        # Apply professional formatting
        try:
            from openpyxl import load_workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
            
            wb = load_workbook(file_path)
            ws = wb.active
            
            # Style definitions
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            total_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
            total_font = Font(bold=True, size=11)
            border_side = Side(style='thin', color='000000')
            border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
            
            # Format header row
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = border
            
            # Format number columns (Plafon, O/S, Angsuran) with thousand separator
            number_columns = ['B', 'D', 'I']  # Plafon, O/S, Angsuran
            for col in number_columns:
                for row in range(2, ws.max_row + 1):
                    cell = ws[f'{col}{row}']
                    cell.number_format = '#,##0'  # Thousand separator, no decimals
                    cell.alignment = Alignment(horizontal='right')
                    cell.border = border
            
            # Format other columns
            for row in range(2, ws.max_row + 1):
                for col in ['A', 'C', 'E', 'F', 'G', 'H']:  # Text columns
                    cell = ws[f'{col}{row}']
                    cell.alignment = Alignment(horizontal='left' if col == 'A' else 'center')
                    cell.border = border
            
            # Add Total row
            total_row = ws.max_row + 1
            ws[f'A{total_row}'] = 'Total'
            ws[f'A{total_row}'].font = total_font
            ws[f'A{total_row}'].fill = total_fill
            ws[f'A{total_row}'].border = border
            
            # Add SUM formulas for numeric columns
            ws[f'B{total_row}'] = f'=SUM(B2:B{total_row-1})'  # Plafon
            ws[f'D{total_row}'] = f'=SUM(D2:D{total_row-1})'  # O/S
            ws[f'I{total_row}'] = f'=SUM(I2:I{total_row-1})'  # Angsuran
            
            # Format total row cells
            for col in ['B', 'D', 'I']:
                cell = ws[f'{col}{total_row}']
                cell.font = total_font
                cell.fill = total_fill
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal='right')
                cell.border = border
            
            # Empty cells in total row
            for col in ['C', 'E', 'F', 'G', 'H']:
                cell = ws[f'{col}{total_row}']
                cell.fill = total_fill
                cell.border = border
            
            # Adjust column widths
            ws.column_dimensions['A'].width = 30  # Nama Bank
            ws.column_dimensions['B'].width = 18  # Plafon
            ws.column_dimensions['C'].width = 12  # Yield
            ws.column_dimensions['D'].width = 18  # O/S
            ws.column_dimensions['E'].width = 16  # Tanggal Pencairan
            ws.column_dimensions['F'].width = 18  # Tanggal Jatuh Tempo
            ws.column_dimensions['G'].width = 10  # Jk Waktu
            ws.column_dimensions['H'].width = 8   # Kol
            ws.column_dimensions['I'].width = 18  # Angsuran
            
            # Save
            wb.save(file_path)
            logger.info("✅ IDEB Excel formatted with totals")
        except Exception as e:
            logger.warning(f"⚠️ Could not apply formatting: {e}")
            # File still exists, just without fancy formatting
    else:
        filename = f"mutasi_{mode}_{user_id}_{timestamp}.xlsx"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if mode == 'daily':
            # Daily balance
            df_export = df.groupby(pd.to_datetime(df['Date']).dt.date).last()[['Balance']].reset_index()
            df_export.columns = ['Tanggal', 'Saldo']
            df_export.to_excel(file_path, index=False, sheet_name='Saldo Harian')
        else:
            # Full scan
            df.to_excel(file_path, index=False, sheet_name='Transactions')
    
    return file_path


def export_to_csv(df, mode, result, user_id):
    """Export DataFrame to CSV"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    if mode == 'ideb':
        filename = f"ideb_slik_{user_id}_{timestamp}.csv"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        df.to_csv(file_path, index=False)
    else:
        filename = f"mutasi_{mode}_{user_id}_{timestamp}.csv"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if mode == 'daily':
            df_export = df.groupby(pd.to_datetime(df['Date']).dt.date).last()[['Balance']].reset_index()
            df_export.columns = ['Tanggal', 'Saldo']
            df_export.to_csv(file_path, index=False)
        else:
            df.to_csv(file_path, index=False)
    
    return file_path


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Terjadi error. Silakan coba lagi atau hubungi admin."
        )


def main():
    """Main function to run bot"""
    print("🤖 Starting MURENA Telegram Bot...")
    print(f"📱 Authorized User ID: {AUTHORIZED_USER_ID}")
    
    # Check if this is a restart (create marker file on startup)
    import os
    restart_marker = os.path.join(TEMP_FOLDER, '.restart_marker')
    should_send_restart_notification = False
    
    # Check for restart marker before creating application
    if os.path.exists(restart_marker):
        print("✅ Bot restarted successfully! Will send notification...")
        should_send_restart_notification = True
        # Remove marker immediately
        try:
            os.remove(restart_marker)
        except:
            pass
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Send restart notification using post_init hook
    async def post_init(app):
        if should_send_restart_notification:
            try:
                await app.bot.send_message(
                    chat_id=AUTHORIZED_USER_ID,
                    text="✅ *Bot Restarted Successfully!*\n\n"
                         "Semua fitur terbaru sudah aktif.\n"
                         "Bot siap digunakan! 🚀",
                    parse_mode='Markdown'
                )
                print("📨 Restart notification sent!")
            except Exception as e:
                print(f"⚠ Failed to send restart notification: {e}")
    
    application.post_init = post_init
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mutasi", mutasi))
    application.add_handler(CommandHandler("saldo", saldo))
    application.add_handler(CommandHandler("ideb", ideb))
    application.add_handler(CommandHandler("export", export_results))
    application.add_handler(CommandHandler("restart", restart_bot))
    
    # Document handler
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
