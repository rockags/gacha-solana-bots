/**
 * ⚡ HIGH-FREQUENCY GACHA BOT (Node.js Starter Kit)
 * ------------------------------------------------
 * Connects to Solana Gacha Protocol WebSocket and runs rolls at up to 30 TPS.
 * 
 * Requirements:
 *   npm install ws
 *   node bot_node.js
 */

const WebSocket = require('ws');

const SERVER_WS = process.env.WS_URL || 'wss://gacha-protocol-628421927095.us-central1.run.app/ws';
const BOT_ID = `node_trader_${Date.now().toString(36)}`;
const TIER = 'bronze'; // 'bronze' ($1.00 pack, $0.002 fee) or 'gold' ($10.00 pack, $0.02 fee)

console.log(`\n======================================================`);
console.log(`🤖 SOLANA GACHA BOT (Node.js High-Frequency Client)`);
console.log(`- Endpoint : ${SERVER_WS}`);
console.log(`- Bot ID   : ${BOT_ID}`);
console.log(`- Pack     : ${TIER.toUpperCase()}`);
console.log(`======================================================\n`);

let rollsCount = 0;
let jackpotsCount = 0;

const ws = new WebSocket(SERVER_WS);

ws.on('open', () => {
  console.log('⚡ Connected to protocol WebSocket!');
  ws.send(JSON.stringify({
    action: 'auth',
    playerId: BOT_ID,
    clientSeed: `seed_${BOT_ID}`
  }));
  ws.send(JSON.stringify({
    action: 'deposit',
    amount: 50.00
  }));
});

ws.on('message', (raw) => {
  try {
    const data = JSON.parse(raw);

    if (data.type === 'AUTH_SUCCESS') {
      console.log(`✅ Authenticated! Balance: $${data.balance.toFixed(2)} USD | Pot: $${data.currentPot.toFixed(4)} USD`);
      // Start rolling
      ws.send(JSON.stringify({ action: 'open_pack', tier: TIER }));
    }

    if (data.type === 'PACK_RESULT') {
      rollsCount++;
      if (data.isJackpot) {
        jackpotsCount++;
        console.log(`\n🎉🎉🎉 ¡¡¡JACKPOT HIT!!! ${BOT_ID} won $${data.jackpotWon.toFixed(2)} USD! (Roll #${data.roll})\n`);
      } else if (rollsCount % 10 === 0) {
        process.stdout.write(`\r[${new Date().toLocaleTimeString()}] Rolls: ${rollsCount} | Pot: $${data.currentPot.toFixed(4)} USD | Last Payout: +$${data.payout.toFixed(3)}   `);
      }
      
      // Cadence throttle (~20 requests/sec)
      setTimeout(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'open_pack', tier: TIER }));
        }
      }, 50);
    }

    if (data.type === 'JACKPOT_ALERT') {
      console.log(`\n💥 Jackpot alert: ${data.winner} won $${data.jackpotAmount.toFixed(2)} USD!`);
    }
  } catch (err) {
    // Ignore JSON parse errors
  }
});

ws.on('error', (err) => {
  console.error('WebSocket Error:', err.message);
});

ws.on('close', () => {
  console.log('\nConnection closed.');
  process.exit(0);
});
