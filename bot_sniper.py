"""
⚡ GACHA QUANT SNIPER BOT (Python Starter Kit)
-----------------------------------------------
High-Frequency Trading & Expected Value (+EV) Sniper for Solana Gacha Protocol.

Strategy:
- Listens to real-time WebSocket ticker.
- When Pot < $15.00: Standby mode.
- When Pot >= $15.00 (+EV): High-frequency burst (20-30 pings/sec) targeting the jackpot.
- On Jackpot Hit: Logs event and resets to standby.

Requirements:
pip install websocket-client
"""

import json
import time
import sys
import threading

try:
    import websocket
except ImportError:
    print("❌ Missing 'websocket-client' library.")
    print("Install via: pip install websocket-client")
    sys.exit(1)

SERVER_WS = "wss://gacha-protocol-628421927095.us-central1.run.app/ws"
BOT_ID = f"python_sniper_{int(time.time()) % 1000}"
EV_THRESHOLD = 15.00  # Trigger sniper burst when Pot >= $15.00 (+EV)
PACK_TIER = "bronze"  # 'bronze' ($1.00 pack, $0.002 fee) or 'gold' ($10.00 pack, $0.02 fee)

current_pot = 10.00
balance = 25.00
is_attacking = False
attack_thread = None
ws_conn = None

def on_message(ws, message):
    global current_pot, balance, is_attacking
    data = json.loads(message)
    msg_type = data.get("type")

    if msg_type == "AUTH_SUCCESS":
        balance = data.get("balance", balance)
        current_pot = data.get("currentPot", current_pot)
        print(f"✅ Bot authenticated as: {BOT_ID} | Balance: ${balance:.2f} USD | Pot: ${current_pot:.4f}")

    elif msg_type == "TICKER":
        current_pot = data.get("pot", current_pot)
        
        # Check +EV condition
        if current_pot >= EV_THRESHOLD and not is_attacking and balance >= 1.00:
            print(f"\n🚨 [+EV ALERT!] Pot reached ${current_pot:.4f} USD (Threshold: ${EV_THRESHOLD:.2f}). LAUNCHING BURST!")
            is_attacking = True
            start_sniper_burst(ws)
        elif current_pot < EV_THRESHOLD and is_attacking:
            print(f"🛑 [STANDBY] Pot dropped to ${current_pot:.4f}. Pausing burst.")
            is_attacking = False

    elif msg_type == "PACK_RESULT":
        if data.get("playerId") == BOT_ID:
            balance = data.get("balance", balance)
            is_jackpot = data.get("isJackpot", False)
            if is_jackpot:
                print(f"\n🎉🎉🎉 ¡¡¡JACKPOT HIT BY {BOT_ID}!!! Won: +${data.get('jackpotWon', 0):.2f} USD")
                print(f"💰 New Balance: ${balance:.2f} USD\n")
            else:
                card = data.get("card", {})
                print(f"📦 Pull: {card.get('name')} ({card.get('rarity')}) | Roll: #{data.get('roll')} | Payout: +${data.get('payout'):.3f} | Pot: ${data.get('currentPot'):.4f}")

    elif msg_type == "JACKPOT_ALERT":
        winner = data.get("winner")
        won = data.get("jackpotAmount", 0)
        print(f"💥 Jackpot claimed by {winner} (${won:.2f} USD). Pot reset.")
        is_attacking = False

def start_sniper_burst(ws):
    def burst():
        global is_attacking, balance
        while is_attacking and balance >= 1.00:
            try:
                ws.send(json.dumps({"action": "open_pack", "tier": PACK_TIER}))
                time.sleep(0.04)  # ~25 requests/sec
            except Exception:
                break
        is_attacking = False

    t = threading.Thread(target=burst, daemon=True)
    t.start()

def on_open(ws):
    print(f"⚡ Connected to Solana Gacha Protocol at {SERVER_WS}")
    ws.send(json.dumps({
        "action": "auth",
        "playerId": BOT_ID,
        "clientSeed": f"seed_{BOT_ID}"
    }))
    ws.send(json.dumps({
        "action": "deposit",
        "amount": 25.00
    }))

def on_error(ws, error):
    print(f"⚠️ Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("🔌 Connection closed. Reconnecting in 2s...")
    time.sleep(2)

if __name__ == "__main__":
    print("======================================================")
    print("🎯 SOLANA GACHA QUANT SNIPER BOT (+EV HUNTER) 🎯")
    print(f"- Server  : {SERVER_WS}")
    print(f"- Target  : Pot >= ${EV_THRESHOLD:.2f} USD (+EV)")
    print(f"- Tier    : {PACK_TIER.upper()}")
    print("======================================================\n")
    
    ws_conn = websocket.WebSocketApp(
        SERVER_WS,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws_conn.run_forever()
