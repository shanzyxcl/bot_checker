import makeWASocket, { DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } from '@whiskeysockets/baileys';
import { Boom } from '@hapi/boom';
import P from 'pino';
import fs from 'fs';

const logger = P({ level: 'silent' });

async function checkWhatsAppNumber(phoneNumber) {
    const { state, saveCreds } = await useMultiFileAuthState('./auth_info_baileys');
    const { version } = await fetchLatestBaileysVersion();
    
    const sock = makeWASocket({
        version,
        logger,
        printQRInTerminal: true,
        auth: state,
        getMessage: async (key) => ({ conversation: '' })
    });

    return new Promise((resolve, reject) => {
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            if (qr) {
                console.log('QR_CODE:', qr);
            }
            
            if (connection === 'close') {
                const shouldReconnect = (lastDisconnect?.error instanceof Boom) &&
                    lastDisconnect.error.output.statusCode !== DisconnectReason.loggedOut;
                if (!shouldReconnect) {
                    reject(new Error('Connection closed'));
                }
            } else if (connection === 'open') {
                try {
                    const jid = phoneNumber.replace(/[^0-9]/g, '') + '@s.whatsapp.net';
                    const [result] = await sock.onWhatsApp(jid);
                    
                    let profilePic = null;
                    let bio = null;
                    let isBusiness = false;
                    
                    if (result && result.exists) {
                        try {
                            profilePic = await sock.profilePictureUrl(jid, 'image');
                        } catch (e) {
                            profilePic = null;
                        }
                        
                        try {
                            const status = await sock.fetchStatus(jid);
                            bio = status?.status || null;
                        } catch (e) {
                            bio = null;
                        }
                        
                        try {
                            const businessProfile = await sock.getBusinessProfile(jid);
                            isBusiness = !!businessProfile;
                        } catch (e) {
                            isBusiness = false;
                        }
                    }
                    
                    const resultData = {
                        exists: result?.exists || false,
                        jid: result?.jid || jid,
                        isBusiness,
                        profilePic,
                        bio
                    };
                    
                    console.log('RESULT:', JSON.stringify(resultData));
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
