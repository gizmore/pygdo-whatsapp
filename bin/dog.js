console.log('Running pygdo whatsapp dog...');

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const path = require('node:path');
var fs = require('fs');
var net = require('net');
var readline = require('readline');
//var chokidar = require('chokidar');

var incomingFilePath = path.join(__dirname, 'wapp.in');
var outgoingFilePath = path.join(__dirname, 'wapp.out');
var incomingStream = null;

function writeIncoming(payload) {
    if (!incomingStream || incomingStream.destroyed) {
        incomingStream = fs.createWriteStream(incomingFilePath, {flags: 'a'});
        incomingStream.on('error', (err) => {
            console.error('Incoming FIFO writer failed:', err);
            incomingStream = null;
        });
    }
    incomingStream.write(payload, (err) => {
        if (err) {
            console.error('Failed to write incoming WhatsApp message:', err);
            incomingStream = null;
        }
    });
}

// Create a new client instance
const client = new Client({
    authStrategy: new LocalAuth(),
    // Keep WhatsApp Web visible while the connector is paired and supervised.
    puppeteer: {
        headless: false,
        // Use the maintained system browser instead of requiring Puppeteer's
        // per-user Chrome download cache.
        executablePath: '/usr/bin/chromium',
    },
});

// When the client is ready, run this code (only once)
client.once('ready', () => {
    console.error('Client is ready!');
    startOutgoingMessageHandler();
});

client.on('authenticated', () => {
    console.error('AUTHENTICATED');
});

client.on('auth_failure', msg => {
    console.error('AUTHENTICATION FAILURE', msg);
    process.exit(1);
});

client.on('ready', () => {
    console.error('READY');
});

client.on('qr', (qr) => {
    qrcode.generate(qr, {small: true});
});

client.on('message', async msg => {
  try {
    console.log(msg.body);
    // Do not ask WhatsApp Web for the chat here. Its page is sometimes
    // reloaded while dispatching a message, which destroys that context.
    // These fields are carried by the event itself.
    const isGroup = msg.from.endsWith('@g.us');
    const userId = isGroup ? (msg.author || msg.from) : msg.from;
    const channelId = isGroup ? msg.from : '';
    const displayname = msg._data.notifyName || '';
    console.log(`FROM ${userId}`);
    if (msg.body.startsWith('!join ')) {
        const inviteCode = msg.body.split(' ')[1];
        try {
            await client.acceptInvite(inviteCode);
            await client.sendMessage(msg.from, 'Joined the group!');
        } catch (e) {
            await client.sendMessage(msg.from, 'That invite code seems to be invalid.');
        }
    }
    else {
        const payload = JSON.stringify({
            user_id: userId,
            displayname,
            phone: null,
            channel_id: channelId,
            channel_name: channelId,
            message: msg.body,
        }) + '\n';
        writeIncoming(payload);
    }
  }
  catch (err) {
    // WhatsApp Web can replace its execution context while a message event is
    // being delivered.  Drop that single event; do not take the connector down.
    console.error('Failed to process incoming WhatsApp message:', err);
  }
});

client.initialize();

function startOutgoingMessageHandler() {
    console.log("Opening ", outgoingFilePath, "for sending from it...");
    const stream = fs.createReadStream(outgoingFilePath, { encoding: 'utf8', flags: 'r' });
    const rl = readline.createInterface({
        input: stream,
        output: process.stdout,
        terminal: false
    });

    rl.on('line', (line) => {
        console.log("FROM OUT:", line)
        line = line.trim()
        if (line !== '') {
            let payload;
            try {
                payload = JSON.parse(line);
            } catch (err) {
                console.error('Ignoring invalid outgoing WhatsApp JSON:', err);
                return;
            }
            if (typeof payload.target !== 'string' || typeof payload.message !== 'string') {
                console.error('Ignoring incomplete outgoing WhatsApp JSON.');
                return;
            }
            client.sendMessage(payload.target, payload.message).then(response => {
                console.log(`Message sent to ${payload.target}: ${payload.message}`);
            }).catch(err => {
                console.error('Failed to send message:', err);
            });
        }
    });

    rl.on('close', () => {
        console.log('Outgoing message handler closed. Reopening...');
        setTimeout(startOutgoingMessageHandler, 1000);  // Reopen the stream after a short delay
    });

    rl.on('error', (err) => {
        console.error('Error reading from outgoing file:', err);
        setTimeout(startOutgoingMessageHandler, 1000);  // Retry after a delay if there's an error
    });
}



//function startOutgoingMessageHandler() {
//    console.log("Open ", outgoingFilePath, "for sending from it...");
//    fs.open(outgoingFilePath, fs.constants.O_RDONLY | fs.constants.O_NONBLOCK, (err, fd) => {
//        console.error(err);
//        const pipe = new net.Socket({ fd });
//        console.log(pipe, fd);
//        pipe.on('data', (data) => {
//            line = data.toString().trim();
//            console.log("FROM OUT:", line)
//            var arr = line.split(':'),
//            args = arr.splice(0,2);
//            line = arr.join(":")
//            const [targetUser, targetChannel] = args;
//            console.log(targetUser, targetChannel);
//            client.sendMessage(targetUser, line).then(response => {
//                console.log(`Message sent to ${targetUser} on ${targetChannel}: ${line}`);
//            }).catch(err => {
//                console.error('Failed to send message:', err);
//            });
//        });
//        pipe.on('error', (err) => {
//            console.error('Error reading from outgoing file:', err);
//        });
//    });
//}
