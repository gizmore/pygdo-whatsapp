const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const incomingFilePath = path.join(__dirname, 'bin', 'wapp.in');
const outgoingFilePath = path.join(__dirname, 'bin', 'wapp.out');

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
    console.log('Client is ready!');
    startOutgoingMessageHandler();
});

client.on('authenticated', () => {
    console.log('AUTHENTICATED');
});

client.on('auth_failure', msg => {
    console.error('AUTHENTICATION FAILURE', msg);
    process.exit(1);
});

client.on('ready', () => {
    console.log('READY');
});

client.on('qr', (qr) => {
    qrcode.generate(qr, {small: true});
});

client.on('message', async msg => {
    chat = msg.getChat()
    contact = msg.getContact();
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
        if (chat.isGroup) {
            const formattedMessage = `${contact.number}:${contact.name}:${chat.id}:${chat.name}:${msg.body}\n`;
        }
        else {
            const formattedMessage = `${contact.number}:${contact.name}:::${msg.body}\n`;
        }
        fs.appendFile(incomingFilePath, formattedMessage, (err) => {
            if (err) {
                console.error('Failed to write incoming message to file:', err);
            }
        });
    }
});

client.initialize();


function startOutgoingMessageHandler() {
    const outStream = fs.createReadStream('bin/wapp.out', { encoding: 'utf8', flag: 'a+' });

    const rl = readline.createInterface({
        input: outStream,
        output: process.stdout,
        terminal: false
    });

    rl.on('line', (line) => {
        const [targetUser, targetChannel, message] = line.split(':');
        client.sendMessage(targetUser, message).then(response => {
            console.log(`Message sent to ${targetUser} on ${targetChannel}: ${message}`);
        }).catch(err => {
            console.error('Failed to send message:', err);
        });
    });

    rl.on('error', (err) => {
        console.error('Error reading from outgoing message stream:', err);
    });
}
