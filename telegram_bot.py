#!/usr/bin/env python3
import asyncio
import subprocess
import json
import re
import os
import tempfile
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Config - GANTI TOKEN BOT LU DISINI
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

def format_phone_number(phone: str, default_country_code: str = None) -> str:
    """Format nomor telepon ke format internasional
    
    Args:
        phone: Nomor telepon
        default_country_code: Kode negara default (contoh: '62' untuk Indonesia, '1' untuk US)
    """
    phone = re.sub(r'[^0-9+]', '', phone)
    
    # Remove leading +
    if phone.startswith('+'):
        phone = phone[1:]
    
    # Kalo udah ada kode negara (panjang > 10)
    if len(phone) >= 10 and not phone.startswith('0'):
        return phone
    
    # Hapus leading 0
    if phone.startswith('0'):
        phone = phone[1:]
    
    # Pake default country code atau Indonesia
    country_code = default_country_code or '62'
    
    return country_code + phone

def parse_phone_list_from_file(content: str) -> list:
    """Parse nomor dari file (support txt, csv)"""
    phones = []
    
    # Split by lines
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # CSV format - ambil kolom pertama
        if ',' in line:
            parts = line.split(',')
            phone = parts[0].strip()
        # Tab separated
        elif '\t' in line:
            parts = line.split('\t')
            phone = parts[0].strip()
        else:
            phone = line
        
        # Clean dan validasi
        phone = re.sub(r'[^0-9+]', '', phone)
        if phone and len(phone) >= 8:  # Minimal 8 digit
            phones.append(phone)
    
    return phones

async def check_wa_number(phone: str) -> dict:
    """Cek nomor WhatsApp via Node.js script"""
    try:
        process = await asyncio.create_subprocess_exec(
            'node', 'wa_checker.mjs', phone,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__)) or '/home/claude'
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        stdout_text = stdout.decode() if stdout else ""
        stderr_text = stderr.decode() if stderr else ""
        
        # Parse output
        result_line = None
        qr_code = None
        
        for line in stdout_text.split('\n'):
            if line.startswith('RESULT:'):
                result_line = line.replace('RESULT:', '').strip()
            elif line.startswith('QR_CODE:'):
                qr_code = line.replace('QR_CODE:', '').strip()
        
        if qr_code:
            return {'status': 'need_qr', 'qr': qr_code}
        
        if result_line:
            return json.loads(result_line)
        
        return {'error': 'No result from checker', 'stderr': stderr_text}
        
    except asyncio.TimeoutError:
        return {'error': 'Timeout - WhatsApp checker took too long'}
    except Exception as e:
        return {'error': str(e)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler command /start"""
    welcome_text = """
🤖 *WA Number Checker Bot*

Kirim nomor WhatsApp yang mau dicek.

*Format nomor:*
🇮🇩 Indonesia: 08123456789 atau 628123456789
🇺🇸 USA: +1234567890 atau 11234567890
🇸🇬 Singapore: +6591234567 atau 6591234567
🇲🇾 Malaysia: +60123456789 atau 60123456789
(Semua negara support!)

*Atau kirim file:*
📁 Upload file .txt atau .csv berisi list nomor
Format file:
```
+628123456789
628987654321
08111222333
```

Bot akan cek:
✅ Nomor terdaftar atau tidak
📸 Ada foto profil atau tidak
💼 WA Biasa atau WA Bisnis
📝 Bio/Status

*Commands:*
/start - Help
/check <nomor> - Cek satu nomor
/country <kode> - Set country code default (contoh: /country 1 untuk US)

Kirim nomor atau file sekarang!
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def set_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler command /country untuk set default country code"""
    if not context.args:
        await update.message.reply_text(
            "❌ Format: /country <kode negara>\n\n"
            "Contoh:\n"
            "/country 62 - Indonesia\n"
            "/country 1 - USA/Canada\n"
            "/country 65 - Singapore\n"
            "/country 60 - Malaysia\n"
            "/country 44 - UK"
        )
        return
    
    country_code = context.args[0].strip()
    
    # Validasi
    if not country_code.isdigit() or len(country_code) > 3:
        await update.message.reply_text("❌ Kode negara harus angka 1-3 digit!")
        return
    
    context.user_data['country_code'] = country_code
    
    country_names = {
        '1': '🇺🇸 USA/Canada',
        '62': '🇮🇩 Indonesia',
        '65': '🇸🇬 Singapore',
        '60': '🇲🇾 Malaysia',
        '44': '🇬🇧 UK',
        '91': '🇮🇳 India',
        '86': '🇨🇳 China',
        '81': '🇯🇵 Japan',
        '82': '🇰🇷 South Korea',
        '61': '🇦🇺 Australia'
    }
    
    country_name = country_names.get(country_code, f'Country +{country_code}')
    
    await update.message.reply_text(
        f"✅ Default country code diset ke: *+{country_code}* ({country_name})\n\n"
        f"Nomor tanpa kode negara akan otomatis ditambah +{country_code}",
        parse_mode='Markdown'
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler command /check untuk cek satu nomor"""
    if not context.args:
        await update.message.reply_text("❌ Format: /check <nomor>\nContoh: /check 628123456789")
        return
    
    phone = ' '.join(context.args)
    country_code = context.user_data.get('country_code', '62')
    
    await process_single_number(update, phone, country_code)

async def process_single_number(update: Update, phone: str, country_code: str = '62'):
    """Process satu nomor"""
    phone = format_phone_number(phone, country_code)
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🔍 Mengecek nomor: +{phone}\n"
        "⏳ Tunggu sebentar..."
    )
    
    # Check number
    result = await check_wa_number(phone)
    
    # Handle QR code requirement
    if result.get('status') == 'need_qr':
        await processing_msg.edit_text(
            "⚠️ *Bot belum login ke WhatsApp!*\n\n"
            "Admin perlu scan QR code dulu.\n"
            "QR Code di log server.",
            parse_mode='Markdown'
        )
        return result
    
    # Handle errors
    if 'error' in result:
        await processing_msg.edit_text(
            f"❌ *Error:*\n{result['error']}\n\n"
            f"Debug info: {result.get('stderr', 'N/A')}",
            parse_mode='Markdown'
        )
        return result
    
    # Format result
    status_icon = "✅" if result.get('exists') else "❌"
    tipe_icon = "💼" if result.get('isBusiness') else "💬"
    foto_icon = "✅" if result.get('profilePic') else "❌"
    bio_text = result.get('bio', 'Hidden / Kosong')
    
    response = f"""
{status_icon} *+{phone}*
├ Status: {"Terdaftar" if result.get('exists') else "Tidak Terdaftar"}
├ Tipe: {tipe_icon} {"WA Bisnis" if result.get('isBusiness') else "WA Biasa"}
├ Foto Profil: {foto_icon} {"Ada" if result.get('profilePic') else "Tidak Ada"}
└ Bio: _{bio_text}_
    """
    
    # Add profile picture if exists
    if result.get('profilePic'):
        keyboard = [[InlineKeyboardButton("📸 Lihat Foto Profil", url=result['profilePic'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await processing_msg.edit_text(response, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await processing_msg.edit_text(response, parse_mode='Markdown')
    
    return result

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan nomor telepon"""
    user_input = update.message.text.strip()
    
    # Validasi input adalah nomor
    if not re.search(r'\d', user_input):
        await update.message.reply_text(
            "❌ Format salah! Kirim nomor WhatsApp atau upload file.\n"
            "Contoh: 08123456789 atau +628123456789\n\n"
            "Atau upload file .txt berisi list nomor"
        )
        return
    
    country_code = context.user_data.get('country_code', '62')
    await process_single_number(update, user_input, country_code)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk file upload"""
    document = update.message.document
    
    # Check file type
    if document.mime_type not in ['text/plain', 'text/csv', 'application/vnd.ms-excel']:
        await update.message.reply_text(
            "❌ File harus .txt atau .csv!\n\n"
            "Format file:\n"
            "```\n"
            "+628123456789\n"
            "628987654321\n"
            "08111222333\n"
            "```",
            parse_mode='Markdown'
        )
        return
    
    # Check file size (max 5MB)
    if document.file_size > 5 * 1024 * 1024:
        await update.message.reply_text("❌ File terlalu besar! Max 5MB")
        return
    
    status_msg = await update.message.reply_text("📥 Downloading file...")
    
    try:
        # Download file
        file = await context.bot.get_file(document.file_id)
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name
        
        # Read file
        with open(tmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        os.unlink(tmp_path)
        
        # Parse nomor
        phones = parse_phone_list_from_file(content)
        
        if not phones:
            await status_msg.edit_text("❌ Ga ada nomor valid di file!")
            return
        
        if len(phones) > 100:
            await status_msg.edit_text(
                f"⚠️ File berisi {len(phones)} nomor.\n"
                "Max 100 nomor per batch!\n\n"
                "Ambil 100 nomor pertama? Reply dengan 'ya' untuk lanjut."
            )
            return
        
        country_code = context.user_data.get('country_code', '62')
        
        await status_msg.edit_text(
            f"📋 Ditemukan {len(phones)} nomor\n"
            f"⏳ Memproses... (ini bisa lama)\n\n"
            f"Progress: 0/{len(phones)}"
        )
        
        # Process all numbers
        results = []
        success_count = 0
        fail_count = 0
        
        for idx, phone in enumerate(phones, 1):
            formatted_phone = format_phone_number(phone, country_code)
            result = await check_wa_number(formatted_phone)
            
            result['original'] = phone
            result['formatted'] = formatted_phone
            results.append(result)
            
            if result.get('exists'):
                success_count += 1
            elif 'error' not in result:
                fail_count += 1
            
            # Update progress setiap 5 nomor
            if idx % 5 == 0 or idx == len(phones):
                await status_msg.edit_text(
                    f"📋 Ditemukan {len(phones)} nomor\n"
                    f"⏳ Memproses...\n\n"
                    f"Progress: {idx}/{len(phones)}\n"
                    f"✅ Terdaftar: {success_count}\n"
                    f"❌ Tidak: {fail_count}"
                )
            
            # Delay to avoid rate limit
            await asyncio.sleep(2)
        
        # Generate report
        report = "📊 *Hasil Checking:*\n\n"
        report += f"Total: {len(phones)} nomor\n"
        report += f"✅ Terdaftar: {success_count}\n"
        report += f"❌ Tidak terdaftar: {fail_count}\n\n"
        
        # Detailed results
        registered = [r for r in results if r.get('exists')]
        
        if registered:
            report += "*Nomor Terdaftar:*\n"
            for r in registered[:20]:  # Max 20 untuk ga kepanjangan
                tipe = "💼" if r.get('isBusiness') else "💬"
                foto = "📸" if r.get('profilePic') else "❌"
                report += f"\n+{r['formatted']}\n"
                report += f"  {tipe} {'Bisnis' if r.get('isBusiness') else 'Biasa'} | {foto} {'Foto' if r.get('profilePic') else 'No Foto'}\n"
            
            if len(registered) > 20:
                report += f"\n_...dan {len(registered) - 20} lagi_\n"
        
        # Save to file
        output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        output_file.write("WA Number Check Results\n")
        output_file.write("=" * 50 + "\n\n")
        
        for r in results:
            output_file.write(f"Number: +{r['formatted']} (Original: {r['original']})\n")
            output_file.write(f"Status: {'✅ Registered' if r.get('exists') else '❌ Not Registered'}\n")
            if r.get('exists'):
                output_file.write(f"Type: {'💼 Business' if r.get('isBusiness') else '💬 Regular'}\n")
                output_file.write(f"Profile Pic: {'✅ Yes' if r.get('profilePic') else '❌ No'}\n")
                output_file.write(f"Bio: {r.get('bio', 'Hidden/Empty')}\n")
                if r.get('profilePic'):
                    output_file.write(f"Photo URL: {r['profilePic']}\n")
            output_file.write("\n" + "-" * 50 + "\n\n")
        
        output_file.close()
        
        # Send report
        await status_msg.edit_text(report, parse_mode='Markdown')
        
        # Send file
        await update.message.reply_document(
            document=open(output_file.name, 'rb'),
            filename=f'wa_check_results_{update.message.date.strftime("%Y%m%d_%H%M%S")}.txt',
            caption="📁 Hasil lengkap (file)"
        )
        
        os.unlink(output_file.name)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

def main():
    """Main function"""
    print("🚀 Starting WA Checker Bot...")
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Set BOT_TOKEN dulu!")
        print("   Set via environment variable: export BOT_TOKEN='your_token'")
        print("   Atau edit langsung di script")
        return
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("country", set_country))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    print("✅ Bot running... Press Ctrl+C to stop")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
