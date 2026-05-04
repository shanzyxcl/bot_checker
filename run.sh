#!/bin/bash

echo "======================================"
echo "  WA Checker Bot - Setup & Runner"
echo "======================================"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js belum terinstall!"
    echo "   Install dulu: https://nodejs.org/"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 belum terinstall!"
    exit 1
fi

# Install Node dependencies
echo "📦 Installing Node.js dependencies..."
npm install --silent

if [ $? -ne 0 ]; then
    echo "❌ Gagal install Node.js dependencies"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    echo "❌ Gagal install Python dependencies"
    exit 1
fi

# Check if bot token is set
if grep -q "YOUR_BOT_TOKEN_HERE" telegram_bot.py; then
    echo ""
    echo "⚠️  BOT TOKEN BELUM DISET!"
    echo ""
    echo "1. Buka @BotFather di Telegram"
    echo "2. Kirim /newbot dan ikutin instruksi"  
    echo "3. Copy token yang dikasih"
    echo "4. Edit telegram_bot.py, ganti YOUR_BOT_TOKEN_HERE dengan token lu"
    echo ""
    read -p "Udah set token? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Setup dibatalin. Set token dulu ya!"
        exit 0
    fi
fi

# Check WhatsApp session
if [ ! -d "auth_info_baileys" ]; then
    echo ""
    echo "📱 WhatsApp belum login!"
    echo "   Scan QR code yang muncul pake WhatsApp lu"
    echo ""
    read -p "Lanjut scan QR? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Setup dibatalin."
        exit 0
    fi
    
    echo ""
    echo "Scanning QR Code... (Ctrl+C kalo udah connect)"
    echo ""
    # Test with dummy number to trigger QR
    node wa_checker.mjs 628123456789
fi

echo ""
echo "✅ Setup selesai!"
echo ""
echo "🚀 Starting bot..."
echo "   Press Ctrl+C to stop"
echo ""

# Run the bot
python3 telegram_bot.py
