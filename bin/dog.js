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

// Create a new client instance
const client = new Client({
    authStrategy: new LocalAuth(),
    webVersionCache: {
        type: "remote",
        remotePath: "https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html",
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
    chat = await msg.getChat();
    console.log(msg.body);
    contact = msg.getContact();
    console.log(msg)
    if (msg.body.startsWith('!join ')) {
        const inviteCode = msg.body.split(' ')[1];
        try {
            await client.acceptInvite(inviteCode);
            msg.reply('Joined the group!');
        } catch (e) {
            msg.reply('That invite code seems to be invalid.');
        }
    }
    else {
        let formattedMessage = ''
        let displayname = msg._data.notifyName || ''
        if (chat.isGroup) {
            formattedMessage = `${msg.from}:${displayname}:${chat.id}:${chat.name}:${msg.body}\n`;
        }
        else {
            formattedMessage = `${msg.from}:${displayname}:::${msg.body}\n`;
        }
//        console.log(formattedMessage)
        fs.appendFile(incomingFilePath, formattedMessage, (err) => {
            if (err) {
                console.error('Failed to write incoming message to file:', err);
            }
        });
        chat.sendSeen();
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
        if (line.trim() !== '') {
            var arr = line.split(':'),
            args = arr.splice(0,2);
            line = arr.join(":")
            const [targetUser, targetChannel] = args;
//          const [targetUser, targetChannel, messageContent] = line.split('::');
            client.sendMessage(targetUser, line).then(response => {
                console.log(`Message sent to ${targetUser} on ${targetChannel}: ${line}`);
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
