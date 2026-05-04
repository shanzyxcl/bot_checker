FROM node:18-slim

# Install Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY package.json ./
COPY requirements.txt ./

# Install dependencies
RUN npm install
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source files
COPY wa_checker.mjs ./
COPY telegram_bot.py ./

# Volume for persistent WhatsApp session
VOLUME ["/app/auth_info_baileys"]

# Run bot
CMD ["python3", "telegram_bot.py"]
