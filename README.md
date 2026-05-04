# WhatsApp Number Checker Bot - Telegram

Bot Telegram untuk cek info nomor WhatsApp secara massal:
- ✅ Nomor terdaftar atau tidak
- 📸 Ada foto profil atau tidak + link download
- 💼 WA Biasa atau WA Bisnis
- 📝 Bio/Status WhatsApp
- 🌍 Support semua negara (multi-country)
- 📁 Upload file untuk cek banyak nomor sekaligus
- ☁️ Bisa jalan di GitHub Actions 24/7

## Features

### Single Number Check
Kirim satu nomor langsung di chat atau pake command `/check`

### Batch Check via File Upload
Upload file `.txt` atau `.csv` berisi list nomor, bot akan cek semua dan kasih laporan lengkap + file hasil.

Format file:
```txt
+628123456789
628987654321
08111222333
+12025551234
+6591234567
```

### Multi-Country Support
Support semua negara! Set default country code:
```
/country 1    # USA/Canada
/country 62   # Indonesia
/country 65   # Singapore
/country 60   # Malaysia
/country 44   # UK
```

## Quick Start

### Option 1: Local Setup (Recommended untuk pertama kali)

**1. Install Dependencies:**
```bash
npm install
pip install -r requirements.txt
```

**2. Setup Bot Token:**
```bash
# Dapetin token dari @BotFather
export BOT_TOKEN="your_token_here"

# Atau buat file .env
cp .env.example .env
# Edit .env, isi BOT_TOKEN
```

**3. Login WhatsApp (pertama kali):**
```bash
# Scan QR code
node wa_checker.mjs 628123456789
# Scan pake WA di HP, tunggu sampai "Connected"
# Tekan Ctrl+C
```

**4. Run Bot:**
```bash
python3 telegram_bot.py
```

### Option 2: Docker

**Build & Run:**
```bash
# Set token di .env
cp .env.example .env
nano .env

# Run dengan Docker Compose
docker-compose up -d

# First time: scan QR
docker-compose logs -f
# Scan QR yang muncul di logs
# Kalo udah connected, restart
docker-compose restart
```

### Option 3: GitHub Actions (24/7 Bot)

Bot bisa jalan di GitHub Actions gratis!

**Setup:**

1. **Fork/Clone repo ini ke GitHub**

2. **Setup WhatsApp Session:**
   ```bash
   # Di local, scan QR dulu
   node wa_checker.mjs 628123456789
   
   # Commit folder auth_info_baileys
   git add auth_info_baileys/
   git commit -m "Add WhatsApp session"
   git push
   ```

3. **Add Secret di GitHub:**
   - Buka repo di GitHub
   - Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `BOT_TOKEN`
   - Value: token dari @BotFather
   - Save

4. **Enable Actions:**
   - Tab Actions
   - Enable workflows
   - Run workflow manually: "Run workflow"

5. **Bot akan jalan otomatis setiap 6 jam** (atau manual trigger)

**IMPORTANT GitHub Actions Notes:**
- Session WhatsApp akan di-cache otomatis
- Bot max run 6 jam per execution (GitHub limit)
- Workflow auto-restart setiap 6 jam
- Kalo session expired, commit ulang `auth_info_baileys/`

## Usage Guide

### Commands

```
/start          - Help & info
/check <nomor>  - Cek satu nomor
/country <kode> - Set default country code
```

### Single Number

Kirim langsung:
```
08123456789
+628123456789
+12025551234
```

### Batch Check (File Upload)

1. Buat file `.txt` atau `.csv`:
   ```txt
   +628123456789
   628987654321
   08111222333
   +12025551234
   ```

2. Upload ke bot
3. Bot akan cek semua (max 100 nomor per batch)
4. Dapat report + file hasil lengkap

**Output Report:**
```
📊 Hasil Checking:

Total: 25 nomor
✅ Terdaftar: 18
❌ Tidak terdaftar: 7

Nomor Terdaftar:

+628123456789
  💬 Biasa | 📸 Foto

+628987654321
  💼 Bisnis | ❌ No Foto
...
```

## Format Nomor yang Support

Bot otomatis detect & convert:

**Indonesia:**
- `08123456789` → `628123456789`
- `8123456789` → `628123456789`
- `+628123456789` → `628123456789`

**USA/Canada:**
- `2025551234` → `12025551234`
- `+12025551234` → `12025551234`

**Singapore:**
- `91234567` → `6591234567`
- `+6591234567` → `6591234567`

**Atau set country code default:**
```
/country 1
# Sekarang 2025551234 auto jadi 12025551234
```

## Deployment Options

### VPS / Cloud Server

**Ubuntu/Debian:**
```bash
# Install deps
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs python3 python3-pip

# Clone & setup
git clone https://github.com/yourusername/wa-checker-bot
cd wa-checker-bot
npm install
pip3 install -r requirements.txt

# Setup systemd service
sudo nano /etc/systemd/system/wa-bot.service
```

**Service file:**
```ini
[Unit]
Description=WhatsApp Checker Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/wa-checker-bot
Environment="BOT_TOKEN=your_token"
ExecStart=/usr/bin/python3 telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable wa-bot
sudo systemctl start wa-bot
sudo systemctl status wa-bot
```

### Heroku

```bash
# Add buildpacks
heroku buildpacks:add heroku/nodejs
heroku buildpacks:add heroku/python

# Set config
heroku config:set BOT_TOKEN="your_token"

# Deploy
git push heroku main
```

### Railway / Render

1. Connect GitHub repo
2. Set environment variable `BOT_TOKEN`
3. Auto-deploy on push

## Troubleshooting

**Bot ga connect ke WhatsApp:**
- Pastikan udah scan QR code
- Cek folder `auth_info_baileys` ada isinya
- Session expired? Scan QR lagi

**Error "need_qr":**
```bash
# Scan QR lagi
node wa_checker.mjs 628123456789
```

**Bot Telegram ga respond:**
- Cek token bot valid
- Cek internet connection
- Lihat logs: `python3 telegram_bot.py`

**GitHub Actions ga jalan:**
- Cek secret `BOT_TOKEN` udah diset
- Cek folder `auth_info_baileys` udah di-commit
- Lihat logs di tab Actions

**Rate limit / banned:**
- Jangan spam terlalu cepet
- Bot punya delay 2 detik antar cek
- Kalo batch besar, tunggu beberapa menit

## Advanced Configuration

### Custom Delay per Check

Edit `telegram_bot.py`:
```python
# Delay antar check (detik)
await asyncio.sleep(2)  # Ganti jadi 5 untuk lebih safe
```

### Max Batch Size

```python
if len(phones) > 100:  # Ganti jadi 50 atau 200
```

### Country Code Presets

Tambah di `set_country()`:
```python
country_names = {
    '1': '🇺🇸 USA/Canada',
    '62': '🇮🇩 Indonesia',
    '63': '🇵🇭 Philippines',  # Tambah baru
    # ...
}
```

## File Structure

```
.
├── telegram_bot.py          # Main bot script
├── wa_checker.mjs           # WhatsApp checker (Node.js)
├── package.json             # Node dependencies
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image
├── docker-compose.yml       # Docker compose config
├── .github/
│   └── workflows/
│       └── bot.yml          # GitHub Actions workflow
├── auth_info_baileys/       # WhatsApp session (generated)
└── README.md
```

## Security Notes

1. **Bot Token** adalah rahasia, jangan commit ke Git
2. **WhatsApp session** (`auth_info_baileys/`) jangan share
3. Kalo mau public repo, tambah `auth_info_baileys/` ke `.gitignore`
4. Use GitHub Secrets untuk token di Actions
5. Bot ga store nomor yang dicek

## Credits & Tech Stack

- **Baileys** - WhatsApp Web multi-device API
- **python-telegram-bot** - Telegram Bot framework
- **GitHub Actions** - Free CI/CD
- **Docker** - Containerization

## License

MIT - Use freely!

## Support

Issues? Questions?
- Open GitHub Issue
- Telegram: @YourTelegramHandle (optional)
