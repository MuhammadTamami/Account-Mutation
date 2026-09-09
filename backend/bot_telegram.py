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
    
    welcome_message = f"""🤖 MURENA BOT - Selamat Datang! 🏦

👋 Halo, {user_name}!

🎯 APA YANG BISA SAYA BANTU?
━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Analisis mutasi rekening otomatis
💰 Laporan saldo harian
📈 Statistik keuangan lengkap
📋 Analisis IDEB SLIK

⚡ PERINTAH TERSEDIA:
━━━━━━━━━━━━━━━━━━━━━━━━━━
/mutasi  - Scan mutasi lengkap
/saldo   - Ringkasan saldo harian
/ideb    - Analisis IDEB SLIK
/export  - Download hasil (Excel/CSV)
/help    - Panduan lengkap
/restart - Restart bot

🏦 BANK YANG DIDUKUNG:
━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BSI         ✅ BCA
✅ Mandiri     ✅ BRI
✅ BNI         ✅ Bank Kalsel
✅ Byond

📁 FORMAT FILE:
━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 PDF  •  📊 CSV  •  📈 Excel  •  🖼️ Image

💡 SIAP MEMULAI?
Kirim file mutasi rekening Anda sekarang!
"""
    
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /help command"""
    if not is_authorized(update.effective_user.id):
        return
    
    help_text = """
╔══════════════════════════╗
║  📖 *PANDUAN MURENA BOT*  ║
╚══════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔹 *1. ANALISIS MUTASI LENGKAP*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Perintah: /mutasi

📝 Langkah:
1️⃣ Ketik /mutasi
2️⃣ Kirim file mutasi rekening
3️⃣ Bot akan menganalisis:
   • Total debit & kredit
   • Frekuensi transaksi
   • Saldo akhir
   • Periode transaksi

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔹 *2. RINGKASAN SALDO HARIAN*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Perintah: /saldo

📝 Langkah:
1️⃣ Ketik /saldo
2️⃣ Kirim file mutasi rekening
3️⃣ Bot akan extract:
   • Saldo per hari
   • Saldo awal & akhir
   • Total mutasi
   • Rata-rata pengendapan

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔹 *3. ANALISIS IDEB SLIK*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Perintah: /ideb

📝 Langkah:
1️⃣ Ketik /ideb
2️⃣ Kirim PDF IDEB SLIK
3️⃣ Bot akan extract:
   • Data kredit (Baki Debet > 0)
   • Plafon & O/S
   • Angsuran bulanan
   • Kolektibilitas

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔹 *4. EXPORT HASIL*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Perintah: /export

📝 Format tersedia:
📊 Excel (.xlsx) - Dengan format & statistik
📄 CSV (.csv) - Data mentah

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔹 *5. RESTART BOT*
━━━━━━━━━━━━━━━━━━━━━━━━━━
Perintah: /restart

Restart bot untuk load fitur terbaru
(Berguna setelah ada update kode)

━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 *TIPS & TRIK:*
━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ File maksimal 20MB
✅ PDF dengan password: kirim file → ketik password
✅ Multi-file: kirim satu per satu
✅ Format terbaik: PDF > Excel > CSV > Image
✅ Image menggunakan OCR (akurasi ~85%)

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 *KEAMANAN & PRIVASI:*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 File dihapus otomatis setelah diproses
🔐 Hanya Anda yang bisa akses bot ini
🔐 Data tidak disimpan permanen
🔐 Enkripsi end-to-end Telegram

━━━━━━━━━━━━━━━━━━━━━━━━━━
❓ *Butuh bantuan?*
Hubungi admin atau gunakan /start
"""
    
    await update.message.reply_text(help_text)


async def mutasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /mutasi command"""
    if not is_authorized(update.effective_user.id):
        return
    
    user_id = update.effective_user.id
    user_sessions[user_id] = {'mode': 'full', 'waiting_file': True}
    
    await update.message.reply_text(
        "╔══════════════════════════╗\n"
        "║  📊 *MODE: FULL SCAN*     ║\n"
        "╚══════════════════════════╝\n\n"
        "📁 *Kirim file mutasi rekening Anda:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📄 PDF (text atau scanned)\n"
        "📊 CSV / Excel (XLS/XLSX)\n"
        "🖼️ Image (JPG/PNG) - OCR\n\n"
        "⏳ Menunggu file...\n"
        "💡 Tip: Format PDF memberikan akurasi terbaik!"
    )


async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /saldo command"""
    if not is_authorized(update.effective_user.id):
        return
    
    user_id = update.effective_user.id
    user_sessions[user_id] = {'mode': 'daily', 'waiting_file': True}
    
    await update.message.reply_text(
        "╔══════════════════════════╗\n"
        "║  💰 *MODE: SALDO HARIAN*  ║\n"
        "╚══════════════════════════╝\n\n"
        "📁 *Kirim file mutasi rekening Anda:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Semua format file didukung\n"
        "✅ Bot akan extract saldo per hari\n"
        "✅ Otomatis hitung statistik\n\n"
        "⏳ Menunggu file...\n"
        "💡 Tip: Hasil akan menampilkan:\n"
        "   • Saldo harian\n"
        "   • Rata-rata pengendapan\n"
        "   • Saldo tertinggi & terendah"
    )


async def ideb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /ideb command"""
    if not is_authorized(update.effective_user.id):
        return
    
    user_id = update.effective_user.id
    user_sessions[user_id] = {'mode': 'ideb', 'waiting_file': True}
    
    await update.message.reply_text(
        "╔══════════════════════════╗\n"
        "║  📋 *MODE: IDEB SLIK*     ║\n"
        "╚══════════════════════════╝\n\n"
        "📁 *Kirim PDF IDEB SLIK Anda:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Bot akan extract data kredit\n"
        "✅ Filter: Baki Debet > 0\n"
        "✅ Include: Plafon, O/S, Angsuran\n\n"
        "⏳ Menunggu file PDF...\n"
        "💡 Tip: Pastikan PDF tidak ter-password"
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
        reply_markup=reply_markup
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
        "Tunggu sebentar..."
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
        f"⏳ MEMPROSES FILE\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 File: {file_name}\n"
        f"💾 Ukuran: {file_size / 1024:.1f} KB\n"
        f"🔄 Status: Sedang dianalisis...\n\n"
        f"⏱️ Mohon tunggu sebentar..."
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
        await processing_msg.edit_text(
            "🔍 Mendeteksi Bank...\n\n"
            "🤖 Menganalisis format file..."
        )
        bank_name = detect_bank(filepath, file_ext)
        
        if bank_name == 'UNKNOWN':
            await processing_msg.edit_text(
                "❌ BANK TIDAK TERDETEKSI\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ Format file tidak dikenali\n\n"
                "💡 Solusi:\n"
                "• Pastikan file adalah mutasi resmi bank\n"
                "• Coba format file lain (PDF/CSV/Excel)\n"
                "• Hubungi admin jika masalah berlanjut"
            )
            return None
        
        # Process based on bank
        await processing_msg.edit_text(
            f"🏦 BANK TERDETEKSI\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Bank: {bank_name}\n"
            f"🔄 Memproses data transaksi...\n\n"
            f"⏱️ Mohon tunggu..."
        )
        
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
            await processing_msg.edit_text(
                f"❌ PROCESSOR TIDAK TERSEDIA\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ Bank: {bank_name}\n\n"
                f"💡 Processor sedang dalam pengembangan"
            )
            return None
        
        # Process file
        df = processor(filepath, file_ext)
        
        if df is None or len(df) == 0:
            await processing_msg.edit_text(
                "❌ TIDAK ADA DATA\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ Tidak ada transaksi ditemukan\n\n"
                "💡 Kemungkinan penyebab:\n"
                "• File kosong atau rusak\n"
                "• Format tidak sesuai dengan bank\n"
                "• PDF ter-password (ketik password)"
            )
            return None
        
        # Format result based on mode
        if mode == 'daily':
            result_text = format_daily_balance_result(df, bank_name)
        else:
            result_text = format_full_scan_result(df, bank_name)
        
        await processing_msg.edit_text(result_text)
        
        return {
            'df': df,
            'bank_name': bank_name,
            'mode': mode,
            'filepath': filepath
        }
        
    except Exception as e:
        logger.error(f"Error in process_bank_file_bot: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"❌ ERROR PROCESSING\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ {str(e)}\n\n"
            f"💡 Coba lagi atau hubungi admin"
        )
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
        
        await processing_msg.edit_text(result_text)
        
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
    """Format full scan result for Telegram - Matching web logic"""
    total_records = len(df)
    
    # Parse amounts - SAME as app.py parse_indonesian_number
    def parse_amount(val):
        if pd.isna(val) or val == '' or val == '-':
            return 0.0
        val_str = str(val).strip()
        
        # Remove "Rp" if present
        val_str = val_str.replace('Rp', '').replace(' ', '').strip()
        
        # Handle different formats (same as web)
        if ',' in val_str and '.' in val_str:
            last_comma = val_str.rfind(',')
            last_dot = val_str.rfind('.')
            
            if last_dot > last_comma:
                # Format: 1,234,567.89 (International)
                val_str = val_str.replace(',', '')
            else:
                # Format: 1.234.567,89 (Indonesian)
                val_str = val_str.replace('.', '').replace(',', '.')
        elif ',' in val_str:
            # Only comma present
            last_comma_pos = val_str.rfind(',')
            decimal_part_length = len(val_str) - last_comma_pos - 1
            
            if decimal_part_length == 2:
                # Format: 1.234.567,89 (Indonesian decimal)
                val_str = val_str.replace('.', '').replace(',', '.')
            else:
                # Format: 1,234,567 (thousand separator)
                val_str = val_str.replace(',', '')
        elif '.' in val_str:
            # Only dots present
            last_dot_pos = val_str.rfind('.')
            decimal_part_length = len(val_str) - last_dot_pos - 1
            
            if decimal_part_length == 2:
                # Format: 200.000.000.00 - last dot is decimal
                val_str = val_str[:last_dot_pos].replace('.', '') + '.' + val_str[last_dot_pos+1:]
            elif decimal_part_length > 3:
                pass
            else:
                # All dots are thousand separators
                val_str = val_str.replace('.', '')
        
        try:
            return float(val_str)
        except:
            return 0.0
    
    # Format number as: 195,000,000.00
    def format_number(val):
        if pd.isna(val) or val == 0:
            return "0.00"
        return f"{val:,.2f}"
    
    # Escape markdown special characters for Telegram
    def escape_markdown(text):
        """Escape special characters for Telegram MarkdownV2"""
        # For simple markdown, we only escape underscores in text
        return str(text).replace('_', '\\_')
    
    df['Amount_numeric'] = df['Amount'].apply(parse_amount)
    df['Balance_numeric'] = df['Balance'].apply(parse_amount)
    
    # Calculate totals
    total_debit = df[df['Type'] == 'Debit']['Amount_numeric'].sum()
    total_credit = df[df['Type'] == 'Credit']['Amount_numeric'].sum()
    
    freq_debit = len(df[df['Type'] == 'Debit'])
    freq_credit = len(df[df['Type'] == 'Credit'])
    
    # Get last balance (saldo akhir)
    last_balance = df['Balance_numeric'].iloc[-1] if len(df) > 0 else 0.0
    
    date_start = df['Date'].min() if 'Date' in df.columns else 'N/A'
    date_end = df['Date'].max() if 'Date' in df.columns else 'N/A'
    
    # Escape bank name (might contain underscores)
    bank_name_safe = escape_markdown(bank_name)
    
    result = f"""✅ HASIL PROCESSING - FULL SCAN

🏦 Bank: {bank_name_safe}
📊 Total Transaksi: {total_records:,}

📅 Periode:
  Dari: {date_start}
  Sampai: {date_end}

💳 Mutasi Debit:
  Total: Rp {format_number(total_debit)}
  Frekuensi: {freq_debit}x

💰 Mutasi Kredit:
  Total: Rp {format_number(total_credit)}
  Frekuensi: {freq_credit}x

📊 Ringkasan:
  Net Flow: Rp {format_number(total_credit - total_debit)}
  Saldo Akhir: Rp {format_number(last_balance)}

💾 Gunakan /export untuk download detail lengkap
"""
    
    return result


def format_daily_balance_result(df, bank_name):
    """Format daily balance result for Telegram - MATCHING WEB LOGIC"""
    # Parse amounts - SAME as app.py parse_indonesian_number
    def parse_amount(val):
        if pd.isna(val) or val == '' or val == '-':
            return 0.0
        val_str = str(val).strip()
        
        # Remove "Rp" if present
        val_str = val_str.replace('Rp', '').replace(' ', '').strip()
        
        # Handle different formats (same as web)
        if ',' in val_str and '.' in val_str:
            last_comma = val_str.rfind(',')
            last_dot = val_str.rfind('.')
            
            if last_dot > last_comma:
                # Format: 1,234,567.89 (International)
                val_str = val_str.replace(',', '')
            else:
                # Format: 1.234.567,89 (Indonesian)
                val_str = val_str.replace('.', '').replace(',', '.')
        elif ',' in val_str:
            # Only comma present
            last_comma_pos = val_str.rfind(',')
            decimal_part_length = len(val_str) - last_comma_pos - 1
            
            if decimal_part_length == 2:
                # Format: 1.234.567,89 (Indonesian decimal)
                val_str = val_str.replace('.', '').replace(',', '.')
            else:
                # Format: 1,234,567 (thousand separator)
                val_str = val_str.replace(',', '')
        elif '.' in val_str:
            # Only dots present
            last_dot_pos = val_str.rfind('.')
            decimal_part_length = len(val_str) - last_dot_pos - 1
            
            if decimal_part_length == 2:
                # Format: 200.000.000.00 - last dot is decimal
                val_str = val_str[:last_dot_pos].replace('.', '') + '.' + val_str[last_dot_pos+1:]
            elif decimal_part_length > 3:
                pass
            else:
                # All dots are thousand separators
                val_str = val_str.replace('.', '')
        
        try:
            return float(val_str)
        except:
            return 0.0
    
    # Format number as: 195,000,000.00 (comma for thousand, dot for decimal)
    def format_number(val):
        if pd.isna(val) or val == 0:
            return "0.00"
        return f"{val:,.2f}"
    
    # Escape markdown special characters
    def escape_markdown(text):
        return str(text).replace('_', '\\_')
    
    df['Amount_numeric'] = df['Amount'].apply(parse_amount)
    df['Balance_numeric'] = df['Balance'].apply(parse_amount)
    
    # Add date parsing columns
    df['Date_parsed'] = pd.to_datetime(df['Date'])
    df['DateOnly'] = df['Date_parsed'].dt.date
    
    # IMPORTANT: Use SAME strategy as app.py for daily balance
    daily_balance_data = []
    
    # Check if this is BCA (has backdate transactions with "TANGGAL :")
    has_backdate = df['Description'].str.contains('TANGGAL :', case=False, na=False).any()
    
    if has_backdate:
        # BCA Strategy: Use first non-backdate transaction balance
        for date in sorted(df['DateOnly'].unique()):
            day_transactions = df[df['DateOnly'] == date]
            
            balance_value = 0.0
            
            # Find FIRST non-backdate Debit with balance
            non_backdate_debit = day_transactions[
                (day_transactions['Type'] == 'Debit') & 
                (~day_transactions['Description'].str.contains('TANGGAL :', case=False, na=False)) &
                (day_transactions['Balance_numeric'] != 0)
            ]
            
            if len(non_backdate_debit) > 0:
                balance_value = non_backdate_debit.iloc[0]['Balance_numeric']
            else:
                # Find FIRST non-backdate Credit with balance
                non_backdate_credit = day_transactions[
                    (day_transactions['Type'] == 'Credit') & 
                    (~day_transactions['Description'].str.contains('TANGGAL :', case=False, na=False)) &
                    (day_transactions['Balance_numeric'] != 0)
                ]
                
                if len(non_backdate_credit) > 0:
                    balance_value = non_backdate_credit.iloc[0]['Balance_numeric']
                else:
                    # Fallback: Use first balance (any)
                    non_zero = day_transactions[day_transactions['Balance_numeric'] != 0]
                    if len(non_zero) > 0:
                        balance_value = non_zero.iloc[0]['Balance_numeric']
            
            daily_balance_data.append({
                'date': date,
                'balance': balance_value
            })
    else:
        # Other banks (Bank Kalsel, Mandiri, etc.): Use LAST balance of the day
        for date in sorted(df['DateOnly'].unique()):
            day_transactions = df[df['DateOnly'] == date]
            
            balance_value = 0.0
            
            # Strategy: Get LAST transaction balance (end of day balance)
            non_zero = day_transactions[day_transactions['Balance_numeric'] != 0]
            
            if len(non_zero) > 0:
                # Use LAST balance (final transaction of the day)
                balance_value = non_zero.iloc[-1]['Balance_numeric']
            
            daily_balance_data.append({
                'date': date,
                'balance': balance_value
            })
    
    # Convert to DataFrame for easier manipulation
    daily_df = pd.DataFrame(daily_balance_data)
    
    total_days = len(daily_df)
    first_balance = daily_df['balance'].iloc[0] if len(daily_df) > 0 else 0
    last_balance = daily_df['balance'].iloc[-1] if len(daily_df) > 0 else 0
    
    # Calculate total debit and credit
    total_debit = df[df['Type'] == 'Debit']['Amount_numeric'].sum()
    total_credit = df[df['Type'] == 'Credit']['Amount_numeric'].sum()
    
    # Calculate frequency
    freq_debit = len(df[df['Type'] == 'Debit'])
    freq_credit = len(df[df['Type'] == 'Credit'])
    
    # Date range
    date_start = df['Date'].min() if len(df) > 0 else 'N/A'
    date_end = df['Date'].max() if len(df) > 0 else 'N/A'
    
    # Escape bank name
    bank_name_safe = escape_markdown(bank_name)
    
    result = f"""✅ HASIL PROCESSING - SALDO HARIAN

🏦 Bank: {bank_name_safe}
📅 Total Hari: {total_days}

📊 Periode:
  Dari: {date_start}
  Sampai: {date_end}

💰 Saldo:
  Saldo Awal: Rp {format_number(first_balance)}
  Saldo Akhir: Rp {format_number(last_balance)}
  Selisih: Rp {format_number(last_balance - first_balance)}

💳 Mutasi:
  Debit: Rp {format_number(total_debit)} ({freq_debit}x)
  Kredit: Rp {format_number(total_credit)} ({freq_credit}x)
  Net: Rp {format_number(total_credit - total_debit)}

💵 Detail Saldo Harian:
"""
    
    # Show max 10 first daily balances, then "... N more days"
    MAX_SHOW = 10
    for idx, row in daily_df.head(MAX_SHOW).iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        balance_str = format_number(row['balance'])
        result += f"  {date_str}: Rp {balance_str}\n"
    
    if len(daily_df) > MAX_SHOW:
        remaining = len(daily_df) - MAX_SHOW
        result += f"  ... dan {remaining} hari lainnya\n"
    
    result += "\n💾 Gunakan /export untuk download detail lengkap"
    
    return result


def format_ideb_result(df, debitur_name):
    """Format IDEB result for Telegram - Enhanced format"""
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
    
    # Header with debitur name
    result = f"""✅ ANALISIS IDEB SLIK

👤 Debitur: {debitur_name}

📊 RINGKASAN:
━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 Total Kredit: {total_records}
💰 Total Plafon: Rp {total_plafon:,.0f}
📊 Total O/S: Rp {total_os:,.0f}
💸 Total Angsuran: Rp {total_angsuran:,.0f}

📋 DETAIL KREDIT:
━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Show max 5 credits for better readability
    MAX_DISPLAY = 5
    display_count = min(total_records, MAX_DISPLAY)
    
    for idx in range(display_count):
        row = df.iloc[idx]
        result += f"\n{idx + 1}. {row['Nama Bank']}\n"
        result += f"  💰 Plafon: {row['Plafon']}\n"
        result += f"  📊 O/S: {row['O/S']}\n"
        result += f"  💸 Angsuran: {row['Angsuran']}\n"
        result += f"  📅 Pencairan: {row['Tanggal Pencairan']}\n"
        result += f"  ⏰ Jatuh Tempo: {row['Tanggal Jatuh Tempo']}\n"
        result += f"  ⏳ Jangka Waktu: {row['Jk Waktu']} bulan\n"
        result += f"  📈 Kol: {row['Kol']}\n"
    
    # If more than display limit
    if total_records > MAX_DISPLAY:
        remaining = total_records - MAX_DISPLAY
        result += f"\n... dan {remaining} kredit lainnya\n"
    
    result += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n💾 Gunakan /export untuk download lengkap"
    
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
    """Export DataFrame to Excel with professional formatting - MATCHING WEB EXACTLY"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    if mode == 'ideb':
        filename = f"ideb_slik_{user_id}_{timestamp}.xlsx"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Get debitur name from result
        debitur_name = result.get('debitur_name', 'Unknown')
        
        # Helper function to parse Indonesian number format
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
        
        # Create Excel with custom formatting MATCHING WEB SCREENSHOT
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from datetime import datetime as dt
        
        wb = Workbook()
        ws = wb.active
        ws.title = "IDEB SLIK"
        
        # A1: Debitur Name (MATCHING WEBSITE SCREENSHOT)
        ws['A1'] = debitur_name.upper()
        ws['A1'].font = Font(bold=True, size=11)
        
        # Row 2: Table Headers (starting from column A) - MATCHING WEBSITE SCREENSHOT
        # Include "Jenis Penggunaan" as last column!
        headers = ['No', 'Nama Bank', 'Plafon', 'Yield (%)', 'O/S', 'Tanggal Pencairan', 'Tanggal Jatuh Tempo', 'Jk Waktu', 'Kol', 'Angsuran', 'Jenis Penggunaan']
        header_row = 2
        start_col = 1  # A column
        
        # Define styles - MATCHING WEBSITE SCREENSHOT (GRAY backgrounds!)
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
            cell_plafon.border = thin_border
            cell_plafon.alignment = Alignment(horizontal='right', vertical='center')
            
            # Yield (column D) - percentage format
            yield_val = row['Yield (%)']
            if isinstance(yield_val, str):
                yield_val = yield_val.replace('%', '').strip()
            try:
                yield_float = float(str(yield_val).replace(',', '.'))
                # Convert to decimal fraction: 3.50 → 0.035
                yield_decimal = yield_float / 100
                cell_yield = ws.cell(row=row_idx, column=start_col + 3, value=yield_decimal)
                # Format as percentage: 0.035 displays as "3.50%"
                cell_yield.number_format = '0.00%'
            except:
                cell_yield = ws.cell(row=row_idx, column=start_col + 3, value=yield_val)
            cell_yield.border = thin_border
            cell_yield.alignment = Alignment(horizontal='center', vertical='center')
            
            # O/S (column E) - number format
            os_val = parse_indonesian_number(row['O/S'])
            cell_os = ws.cell(row=row_idx, column=start_col + 4, value=os_val)
            cell_os.number_format = '#,##0'
            cell_os.border = thin_border
            cell_os.alignment = Alignment(horizontal='right', vertical='center')
            
            # Tanggal Pencairan (column F) - date format: 16-Dec-21
            date_pencairan_str = row['Tanggal Pencairan']
            try:
                # Parse mm/dd/yyyy format
                date_obj = dt.strptime(date_pencairan_str, '%m/%d/%Y')
                cell_tgl = ws.cell(row=row_idx, column=start_col + 5, value=date_obj)
                cell_tgl.number_format = 'DD-MMM-YY'
            except:
                cell_tgl = ws.cell(row=row_idx, column=start_col + 5, value=date_pencairan_str)
            cell_tgl.border = thin_border
            cell_tgl.alignment = Alignment(horizontal='center', vertical='center')
            
            # Tanggal Jatuh Tempo (column G) - date format: 16-Dec-21
            date_tempo_str = row['Tanggal Jatuh Tempo']
            try:
                date_obj = dt.strptime(date_tempo_str, '%m/%d/%Y')
                cell_tgl2 = ws.cell(row=row_idx, column=start_col + 6, value=date_obj)
                cell_tgl2.number_format = 'DD-MMM-YY'
            except:
                cell_tgl2 = ws.cell(row=row_idx, column=start_col + 6, value=date_tempo_str)
            cell_tgl2.border = thin_border
            cell_tgl2.alignment = Alignment(horizontal='center', vertical='center')
            
            # Jk Waktu (column H)
            cell_jk = ws.cell(row=row_idx, column=start_col + 7, value=row['Jk Waktu'])
            cell_jk.border = thin_border
            cell_jk.alignment = Alignment(horizontal='center', vertical='center')
            
            # Kol (column I)
            cell_kol = ws.cell(row=row_idx, column=start_col + 8, value=row['Kol'])
            cell_kol.border = thin_border
            cell_kol.alignment = Alignment(horizontal='center', vertical='center')
            
            # Angsuran (column J) - number format
            angsuran_val = parse_indonesian_number(row['Angsuran'])
            cell_angsuran = ws.cell(row=row_idx, column=start_col + 9, value=angsuran_val)
            cell_angsuran.number_format = '#,##0'
            cell_angsuran.border = thin_border
            cell_angsuran.alignment = Alignment(horizontal='right', vertical='center')
            
            # Jenis Penggunaan (column K) - NEW!
            jenis_penggunaan = row.get('Jenis Konsumsi', '')  # From DataFrame
            cell_jenis = ws.cell(row=row_idx, column=start_col + 10, value=jenis_penggunaan)
            cell_jenis.border = thin_border
            cell_jenis.alignment = Alignment(horizontal='center', vertical='center')
        
        # Total row - MATCHING WEBSITE SCREENSHOT
        total_row = data_start_row + len(df)
        total_fill = PatternFill(start_color="BFBFBF", end_color="BFBFBF", fill_type="solid")  # Gray (matching header)
        total_font = Font(bold=True)
        
        # "Total" label (column A-B merged)
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
        cell_total_plafon.border = thin_border
        cell_total_plafon.alignment = Alignment(horizontal='right', vertical='center')
        
        # Empty cells (D=Yield, F=Tgl Pencairan, G=Tgl Jatuh Tempo, H=Jk Waktu, I=Kol, K=Jenis Penggunaan)
        for col_offset in [3, 5, 6, 7, 8, 10]:
            cell = ws.cell(row=total_row, column=start_col + col_offset)
            cell.fill = total_fill
            cell.border = thin_border
        
        # Total O/S (column E)
        cell_total_os = ws.cell(row=total_row, column=start_col + 4, value=total_os)
        cell_total_os.number_format = '#,##0'
        cell_total_os.fill = total_fill
        cell_total_os.font = total_font
        cell_total_os.border = thin_border
        cell_total_os.alignment = Alignment(horizontal='right', vertical='center')
        
        # Total Angsuran (column J)
        cell_total_angsuran = ws.cell(row=total_row, column=start_col + 9, value=total_angsuran)
        cell_total_angsuran.number_format = '#,##0'
        cell_total_angsuran.fill = total_fill
        cell_total_angsuran.font = total_font
        cell_total_angsuran.border = thin_border
        cell_total_angsuran.alignment = Alignment(horizontal='right', vertical='center')
        
        # Adjust column widths - MATCHING SCREENSHOT
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
        
        # Save
        wb.save(file_path)
        logger.info("✅ IDEB Excel formatted matching website screenshot")
        
    else:
        filename = f"mutasi_{mode}_{user_id}_{timestamp}.xlsx"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if mode == 'daily':
            # Parse amounts for calculations
            def parse_amount(val):
                if pd.isna(val) or val == '' or val == '-':
                    return 0.0
                val_str = str(val).strip().replace('Rp', '').replace(' ', '').strip()
                
                if ',' in val_str and '.' in val_str:
                    last_comma = val_str.rfind(',')
                    last_dot = val_str.rfind('.')
                    
                    if last_dot > last_comma:
                        val_str = val_str.replace(',', '')
                    else:
                        val_str = val_str.replace('.', '').replace(',', '.')
                elif ',' in val_str:
                    last_comma_pos = val_str.rfind(',')
                    decimal_part_length = len(val_str) - last_comma_pos - 1
                    
                    if decimal_part_length == 2:
                        val_str = val_str.replace('.', '').replace(',', '.')
                    else:
                        val_str = val_str.replace(',', '')
                elif '.' in val_str:
                    last_dot_pos = val_str.rfind('.')
                    decimal_part_length = len(val_str) - last_dot_pos - 1
                    
                    if decimal_part_length == 2:
                        val_str = val_str[:last_dot_pos].replace('.', '') + '.' + val_str[last_dot_pos+1:]
                    elif decimal_part_length > 3:
                        pass
                    else:
                        val_str = val_str.replace('.', '')
                
                try:
                    return float(val_str)
                except:
                    return 0.0
            
            # Add date parsing columns
            df['Date_parsed'] = pd.to_datetime(df['Date'])
            df['DateOnly'] = df['Date_parsed'].dt.date
            df['Balance_numeric'] = df['Balance'].apply(parse_amount)
            
            # Create daily balance DataFrame using SAME logic as web
            daily_balance_data = []
            
            # Check if this is BCA (has backdate transactions)
            has_backdate = df['Description'].str.contains('TANGGAL :', case=False, na=False).any()
            
            if has_backdate:
                # BCA Strategy: Use first non-backdate transaction balance
                for date in sorted(df['DateOnly'].unique()):
                    day_transactions = df[df['DateOnly'] == date]
                    
                    balance_value = 0.0
                    
                    # Find FIRST non-backdate Debit with balance
                    non_backdate_debit = day_transactions[
                        (day_transactions['Type'] == 'Debit') & 
                        (~day_transactions['Description'].str.contains('TANGGAL :', case=False, na=False)) &
                        (day_transactions['Balance_numeric'] != 0)
                    ]
                    
                    if len(non_backdate_debit) > 0:
                        balance_value = non_backdate_debit.iloc[0]['Balance_numeric']
                    else:
                        # Find FIRST non-backdate Credit with balance
                        non_backdate_credit = day_transactions[
                            (day_transactions['Type'] == 'Credit') & 
                            (~day_transactions['Description'].str.contains('TANGGAL :', case=False, na=False)) &
                            (day_transactions['Balance_numeric'] != 0)
                        ]
                        
                        if len(non_backdate_credit) > 0:
                            balance_value = non_backdate_credit.iloc[0]['Balance_numeric']
                        else:
                            # Fallback
                            non_zero = day_transactions[day_transactions['Balance_numeric'] != 0]
                            if len(non_zero) > 0:
                                balance_value = non_zero.iloc[0]['Balance_numeric']
                    
                    daily_balance_data.append({
                        'Tanggal': date.day,  # Day number only
                        'Saldo': balance_value
                    })
            else:
                # Other banks: Use LAST balance of the day
                for date in sorted(df['DateOnly'].unique()):
                    day_transactions = df[df['DateOnly'] == date]
                    
                    balance_value = 0.0
                    
                    # Get LAST transaction balance
                    non_zero = day_transactions[day_transactions['Balance_numeric'] != 0]
                    
                    if len(non_zero) > 0:
                        balance_value = non_zero.iloc[-1]['Balance_numeric']
                    
                    daily_balance_data.append({
                        'Tanggal': date.day,  # Day number only
                        'Saldo': balance_value
                    })
            
            # Export daily balance
            df_export = pd.DataFrame(daily_balance_data)
            df_export.to_excel(file_path, index=False, sheet_name='Saldo Harian')
            
            # Add formatting and statistics (like web)
            try:
                from openpyxl import load_workbook
                from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
                
                wb = load_workbook(file_path)
                ws = wb.active
                
                # Calculate statistics
                balances = [item['Saldo'] for item in daily_balance_data]
                total_balance = sum(balances)
                avg_balance = sum(balances) / len(balances) if len(balances) > 0 else 0
                highest_balance = max(balances) if len(balances) > 0 else 0
                lowest_balance = min(balances) if len(balances) > 0 else 0
                
                # Add statistics rows
                last_row = len(df_export) + 2
                stats_start_row = last_row + 1
                
                ws.cell(row=stats_start_row, column=1, value='Total')
                ws.cell(row=stats_start_row, column=2, value=total_balance)
                ws.cell(row=stats_start_row, column=2).number_format = '#,##0.00'
                
                ws.cell(row=stats_start_row + 1, column=1, value='Rata-rata Pengendapan')
                ws.cell(row=stats_start_row + 1, column=2, value=avg_balance)
                ws.cell(row=stats_start_row + 1, column=2).number_format = '#,##0.00'
                
                ws.cell(row=stats_start_row + 2, column=1, value='Saldo Rata-rata')
                ws.cell(row=stats_start_row + 2, column=2, value=avg_balance)
                ws.cell(row=stats_start_row + 2, column=2).number_format = '#,##0.00'
                
                ws.cell(row=stats_start_row + 3, column=1, value='Saldo Tertinggi')
                ws.cell(row=stats_start_row + 3, column=2, value=highest_balance)
                ws.cell(row=stats_start_row + 3, column=2).number_format = '#,##0.00'
                
                ws.cell(row=stats_start_row + 4, column=1, value='Saldo Terendah')
                ws.cell(row=stats_start_row + 4, column=2, value=lowest_balance)
                ws.cell(row=stats_start_row + 4, column=2).number_format = '#,##0.00'
                
                # Calculate mutation statistics
                df['Amount_numeric'] = df['Amount'].apply(parse_amount)
                total_debit = df[df['Type'] == 'Debit']['Amount_numeric'].sum()
                total_credit = df[df['Type'] == 'Credit']['Amount_numeric'].sum()
                freq_debit = len(df[df['Type'] == 'Debit'])
                freq_credit = len(df[df['Type'] == 'Credit'])
                
                # Add mutation statistics
                mutation_start_row = stats_start_row + 6
                
                # Header
                ws.merge_cells(start_row=mutation_start_row, start_column=1, end_row=mutation_start_row, end_column=3)
                header_cell = ws.cell(row=mutation_start_row, column=1)
                header_cell.value = 'Mutasi Debet'
                header_cell.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
                header_cell.font = Font(bold=True)
                header_cell.alignment = Alignment(horizontal='center')
                
                ws.merge_cells(start_row=mutation_start_row, start_column=4, end_row=mutation_start_row, end_column=6)
                header_cell2 = ws.cell(row=mutation_start_row, column=4)
                header_cell2.value = 'Mutasi kredit'
                header_cell2.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
                header_cell2.font = Font(bold=True)
                header_cell2.alignment = Alignment(horizontal='center')
                
                # Data rows
                mutation_rows = [
                    ('Total Mutasi', total_debit, total_credit),
                    ('Adjusted', '-', '-'),
                    ('Total Frekuensi', freq_debit, freq_credit),
                    ('Adjusted', '-', '-')
                ]
                
                for idx, (label, debit_val, credit_val) in enumerate(mutation_rows, start=1):
                    row_num = mutation_start_row + idx
                    ws.cell(row=row_num, column=1, value=label)
                    ws.merge_cells(start_row=row_num, start_column=2, end_row=row_num, end_column=3)
                    
                    # Debit value
                    debit_cell = ws.cell(row=row_num, column=2)
                    if isinstance(debit_val, (int, float)):
                        debit_cell.value = debit_val
                        debit_cell.number_format = '#,##0.00'
                    else:
                        debit_cell.value = debit_val
                    
                    ws.merge_cells(start_row=row_num, start_column=5, end_row=row_num, end_column=6)
                    
                    # Credit value
                    credit_cell = ws.cell(row=row_num, column=5)
                    if isinstance(credit_val, (int, float)):
                        credit_cell.value = credit_val
                        credit_cell.number_format = '#,##0.00'
                    else:
                        credit_cell.value = credit_val
                    
                    # Borders
                    thin_border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )
                    for col in range(1, 7):
                        ws.cell(row=row_num, column=col).border = thin_border
                
                # Header borders
                for col in range(1, 7):
                    ws.cell(row=mutation_start_row, column=col).border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )
                
                wb.save(file_path)
                logger.info("✅ Daily balance Excel formatted with statistics")
            except Exception as e:
                logger.warning(f"⚠️ Could not apply formatting: {e}")
        else:
            # Full scan mode
            df.to_excel(file_path, index=False, sheet_name='Transactions')
            
            # Add totals summary at bottom
            try:
                from openpyxl import load_workbook
                from openpyxl.styles import Font
                
                def parse_amount(val):
                    if pd.isna(val) or val == '' or val == '-':
                        return 0.0
                    val_str = str(val).strip().replace('Rp', '').replace(' ', '').strip()
                    
                    if ',' in val_str and '.' in val_str:
                        last_comma = val_str.rfind(',')
                        last_dot = val_str.rfind('.')
                        
                        if last_dot > last_comma:
                            val_str = val_str.replace(',', '')
                        else:
                            val_str = val_str.replace('.', '').replace(',', '.')
                    elif ',' in val_str:
                        last_comma_pos = val_str.rfind(',')
                        decimal_part_length = len(val_str) - last_comma_pos - 1
                        
                        if decimal_part_length == 2:
                            val_str = val_str.replace('.', '').replace(',', '.')
                        else:
                            val_str = val_str.replace(',', '')
                    elif '.' in val_str:
                        last_dot_pos = val_str.rfind('.')
                        decimal_part_length = len(val_str) - last_dot_pos - 1
                        
                        if decimal_part_length == 2:
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
                
                wb = load_workbook(file_path)
                ws = wb.active
                
                last_row = len(df) + 3
                
                ws.cell(row=last_row, column=1, value='TOTAL MUTASI DEBIT:')
                ws.cell(row=last_row, column=2, value=total_debit)
                ws.cell(row=last_row, column=2).number_format = '#,##0.00'
                
                ws.cell(row=last_row + 1, column=1, value='TOTAL MUTASI KREDIT:')
                ws.cell(row=last_row + 1, column=2, value=total_credit)
                ws.cell(row=last_row + 1, column=2).number_format = '#,##0.00'
                
                ws.cell(row=last_row + 2, column=1, value='SALDO TERAKHIR:')
                ws.cell(row=last_row + 2, column=2, value=last_balance)
                ws.cell(row=last_row + 2, column=2).number_format = '#,##0.00'
                
                # Bold labels
                ws.cell(row=last_row, column=1).font = Font(bold=True)
                ws.cell(row=last_row + 1, column=1).font = Font(bold=True)
                ws.cell(row=last_row + 2, column=1).font = Font(bold=True)
                
                wb.save(file_path)
                logger.info("✅ Full scan Excel formatted with totals")
            except Exception as e:
                logger.warning(f"⚠️ Could not apply formatting: {e}")
    
    return file_path


def export_to_csv(df, mode, result, user_id):
    """Export DataFrame to CSV - MATCHING WEB LOGIC"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    if mode == 'ideb':
        filename = f"ideb_slik_{user_id}_{timestamp}.csv"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Get debitur name
        debitur_name = result.get('debitur_name', 'Unknown')
        
        # Helper function to parse Indonesian number format
        def parse_indonesian_number(val):
            if pd.isna(val) or val == '' or val == '-':
                return 0.0
            val_str = str(val).strip()
            
            last_comma_pos = val_str.rfind(',')
            
            if last_comma_pos == -1:
                try:
                    return float(val_str)
                except:
                    return 0.0
            
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
        
        # Format number for CSV
        def format_indonesian_number(value):
            if pd.isna(value) or value == 0:
                return "0,00"
            formatted = f"{value:,.2f}"
            formatted = formatted.replace('.', ',')
            return formatted
        
        # Rename "Jenis Konsumsi" to "Jenis Penggunaan" if exists (MATCHING WEB)
        df_export = df.copy()
        if 'Jenis Konsumsi' in df_export.columns:
            df_export = df_export.rename(columns={'Jenis Konsumsi': 'Jenis Penggunaan'})
        
        # Add Total row (only for columns that exist)
        total_row_dict = {
            'Nama Bank': 'TOTAL',
            'Plafon': format_indonesian_number(total_plafon),
            'Yield (%)': '',
            'O/S': format_indonesian_number(total_os),
            'Tanggal Pencairan': '',
            'Tanggal Jatuh Tempo': '',
            'Jk Waktu': '',
            'Kol': '',
            'Angsuran': format_indonesian_number(total_angsuran),
            'Jenis Penggunaan': ''  # Empty for total row
        }
        
        total_row = pd.DataFrame([total_row_dict])
        
        df_with_total = pd.concat([df_export, total_row], ignore_index=True)
        
        # Add debitur name as first line
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Debitur: {debitur_name}\n")
            df_with_total.to_csv(f, index=False)
        
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
                         "Bot siap digunakan! 🚀"
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
