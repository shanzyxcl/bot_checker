import makeWASocket, { DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } from '@whiskeysockets/baileys';
import { Boom } from '@hapi/boom';
import P from 'pino';
import qrcode from 'qrcode-terminal';

const logger = P({ level: 'silent' });

async function checkWhatsAppNumber(phoneNumber) {
    const { state, saveCreds } = await useMultiFileAuthState('./auth_info_baileys');
    const { version } = await fetchLatestBaileysVersion();
    
    const sock = makeWASocket({
        version,
        logger,
        // Removed printQRInTerminal option as it's deprecated
        auth: state,
        getMessage: async (key) => ({ conversation: '' })
    });

    return new Promise((resolve, reject) => {
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            // Display QR code in terminal when available
            if (qr) {
                console.log('\n📱 Scan this QR code with WhatsApp:\n');
                qrcode.generate(qr, { small: true });
                console.log('\nWhatsApp > Settings > Linked Devices > Link a Device\n');
            }
            
            if (connection === 'close') {
                const shouldReconnect = (lastDisconnect?.error instanceof Boom) &&
                    lastDisconnect.error.output.statusCode !== DisconnectReason.loggedOut;
                if (!shouldReconnect) {
                    reject(new Error('Connection closed'));
                }
            } else if (connection === 'open') {
                console.log('✅ Connected to WhatsApp\n');
                try {
                    const jid = phoneNumber.replace(/[^0-9]/g, '') + '@s.whatsapp.net';
                    const [result] = await sock.onWhatsApp(jid);
                    
                    let profilePic = null;
                    let bio = null;
                    let isBusiness = false;
                    
                    if (result && result.exists) {
                        console.log(`✅ Number ${phoneNumber} is on WhatsApp\n`);
                        
                        // Try to get profile picture
                        try {
                            profilePic = await sock.profilePictureUrl(jid, 'image');
                        } catch (e) {
                            profilePic = null;
                        }
                        
                        // Try to get bio/status
                        try {
                            const status = await sock.fetchStatus(jid);
                            bio = status?.status || null;
                        } catch (e) {
                            bio = null;
                        }
                        
                        // Check if business account
                        try {
                            const businessProfile = await sock.getBusinessProfile(jid);
                            isBusiness = !!businessProfile;
                        } catch (e) {
                            isBusiness = false;
                        }
                    } else {
                        console.log(`❌ Number ${phoneNumber} is NOT on WhatsApp\n`);
                    }
                    
                    const resultData = {
                        exists: result?.exists || false,
                        jid: result?.jid || jid,
                        isBusiness,
                        profilePic,
                        bio
                    };
                    
                    console.log('RESULT:', JSON.stringify(resultData, null, 2));
                    await sock.logout();
                    resolve(resultData);
                } catch (error) {
                    reject(error);
                }
            }
        });

        sock.ev.on('creds.update', saveCreds);
    });
}

const number = process.argv[2];
if (!number) {
    console.error('Usage: node wa_checker.mjs <phone_number>');
    process.exit(1);
}

checkWhatsAppNumber(number)
    .then(result => {
        process.exit(0);
    })
    .catch(err => {
        console.error('ERROR:', err.message);
        process.exit(1);
    });
