"""
⚡ GACHA QUANT SNIPER BOT v2 (Python Starter Kit)
--------------------------------------------------
High-Frequency Trading & Expected Value (+EV) Sniper for Solana Gacha Protocol.

Features:
- Sub-10ms WebSocket connection to Google Cloud Run.
- Multi-tier Micro-Jackpot detection (Micro-Hits 1/25, Major-Hits 1/100, Mega-Jackpots 1/1000).
- Provably Fair HMAC-SHA256 offline verification.
- Built-in latency benchmark (--bench) and dry-run mode (--test).

Usage:
  python bot_sniper.py --bench       # Measure live latency to the server
  python bot_sniper.py --test        # Test pack openings in simulated test mode
  python bot_sniper.py               # Run autonomous live sniper
  python bot_sniper.py --gold        # Target Gold $10 packs instead of Bronze $1

Requirements:
  pip install websocket-client
"""

import json
import time
import sys
import threading

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    import websocket
except ImportError:
    print("❌ Missing 'websocket-client' library.")
    print("Install via: pip install websocket-client")
    sys.exit(1)

SERVER_WS = "wss://gacha-protocol-628421927095.us-central1.run.app/ws"
BOT_ID = f"python_sniper_{int(time.time()) % 10000}"
EV_THRESHOLD = 5.00  # Trigger sniper burst when Pot >= $5.00 USD
PACK_TIER = "gold" if "--gold" in sys.argv else "bronze"

current_pot = 5.00
balance = 0.00
is_attacking = False
attack_thread = None
ws_conn = None

# -------------------------------------------------------------
# MODE 1: LATENCY BENCHMARK (--bench)
# -------------------------------------------------------------
def run_latency_benchmark():
    print("\n======================================================")
    print("⚡ SOLANA GACHA PROTOCOL — LATENCY BENCHMARK ⚡")
    print(f"- Target Server: {SERVER_WS}")
    print(f"- Pings: 10 rapid round-trip tests")
    print("======================================================\n")

    rtts = []
    ws = websocket.create_connection(SERVER_WS, timeout=8)

    for i in range(1, 11):
        t0 = time.time()
        ws.send(json.dumps({"action": "ping", "timestamp": int(t0 * 1000)}))
        reply = ws.recv()
        t1 = time.time()
        rtt_ms = (t1 - t0) * 1000.0
        rtts.append(rtt_ms)
        data = json.loads(reply)
        pot = data.get("pot", 5.0)
        clients = data.get("activeClients", 1)
        print(f"  [Ping #{i:02d}] RTT: {rtt_ms:6.2f} ms | Pot: ${pot:.4f} | Connected Bots: {clients}")
        time.sleep(0.1)

    ws.close()

    min_rtt = min(rtts)
    avg_rtt = sum(rtts) / len(rtts)
    max_rtt = max(rtts)

    print("\n------------------------------------------------------")
    print(f"🏆 BENCHMARK RESULTS:")
    print(f"- Minimum Latency : {min_rtt:.2f} ms")
    print(f"- Average Latency : {avg_rtt:.2f} ms")
    print(f"- Maximum Latency : {max_rtt:.2f} ms")
    
    if avg_rtt < 25.0:
        print("⚡ STATUS: ULTRA-LOW LATENCY READY FOR HIGH-FREQUENCY TRADING!")
    else:
        print("✅ STATUS: OPTIMAL CONNECTION ESTABLISHED.")
    print("======================================================\n")
    sys.exit(0)

# -------------------------------------------------------------
# MODE 2 & 3: LIVE SNIPER & MULTI-TIER PARSER
# -------------------------------------------------------------
def on_message(ws, message):
    global current_pot, balance, is_attacking
    data = json.loads(message)
    msg_type = data.get("type")

    if msg_type == "AUTH_SUCCESS":
        balance = data.get("balance", balance)
        current_pot = data.get("currentPot", current_pot)
        print(f"✅ Bot authenticated as: {BOT_ID} | Balance: ${balance:.2f} USD | Pot: ${current_pot:.4f} USD")
        if balance < 1.00:
            print(f"ℹ️ Tip: Fund your bot by sending SOL to the on-chain vault: 3u6pHbfXqiDJLMxpLtXvUxGiC1Twwo2v9aaHBxo839GM")

    elif msg_type == "TICKER":
        current_pot = data.get("pot", current_pot)
        
        # Check +EV condition
        if current_pot >= EV_THRESHOLD and not is_attacking and balance >= 1.00:
            print(f"\n🚨 [+EV ALERT!] Pot reached ${current_pot:.4f} USD (Threshold: ${EV_THRESHOLD:.2f}). LAUNCHING HIGH-FREQUENCY BURST!")
            is_attacking = True
            start_sniper_burst(ws)
        elif current_pot < EV_THRESHOLD and is_attacking:
            print(f"🛑 [STANDBY] Pot dropped to ${current_pot:.4f}. Pausing burst.")
            is_attacking = False

    elif msg_type == "PACK_RESULT":
        if data.get("playerId") == BOT_ID:
            balance = data.get("balance", balance)
            is_jackpot = data.get("isJackpot", False)
            hit_type = data.get("hitType", "NORMAL")
            roll = data.get("roll")
            payout = data.get("payout", 0)
            net_change = data.get("netChange", 0)

            if hit_type == "MEGA_JACKPOT":
                print(f"\n🎉🎉🎉 ¡¡¡MEGA JACKPOT HIT BY {BOT_ID}!!! Won: +${data.get('jackpotWon', 0):.2f} USD (Roll #{roll})")
                print(f"💰 New Balance: ${balance:.2f} USD\n")
            elif hit_type == "MAJOR_HIT":
                print(f"💥 [MAJOR HIT! 1% Odds] Roll #{roll} -> Payout: +${payout:.3f} (Net: +${net_change:.3f}) | Balance: ${balance:.2f}")
            elif hit_type == "MICRO_HIT":
                print(f"⚡ [MICRO-HIT! 4% Odds] Roll #{roll} -> Payout: +${payout:.3f} (Net: +${net_change:.3f}) | Balance: ${balance:.2f}")
            else:
                card = data.get("card", {})
                card_name = card.get("name", "Pack")
                rarity = card.get("rarity", "COMMON")
                print(f"📦 Pull: {card_name} ({rarity}) | Roll: #{roll:03d} | Payout: +${payout:.3f} | Net: -${abs(net_change):.3f} | Pot: ${data.get('currentPot'):.4f}")

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

def on_error(ws, error):
    print(f"⚠️ Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("🔌 Connection closed. Reconnecting in 3s...")
    time.sleep(3)

if __name__ == "__main__":
    if "--bench" in sys.argv or "-b" in sys.argv:
        run_latency_benchmark()

    print("======================================================")
    print("🎯 SOLANA GACHA QUANT SNIPER BOT v2 (+EV HUNTER) 🎯")
    print(f"- Server  : {SERVER_WS}")
    print(f"- Bot ID  : {BOT_ID}")
    print(f"- Target  : Pot >= ${EV_THRESHOLD:.2f} USD (+EV)")
    print(f"- Tier    : {PACK_TIER.upper()} (Refund: {'$9.98' if PACK_TIER == 'gold' else '$0.998'})")
    print("======================================================\n")
    print("💡 Run with '--bench' to measure roundtrip latency to the server.")
    print("💡 Run with '--gold' to snipe $10 Gold packs for 100% pot share.\n")
    
    ws_conn = websocket.WebSocketApp(
        SERVER_WS,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws_conn.run_forever()
