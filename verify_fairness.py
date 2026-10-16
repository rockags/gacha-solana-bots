"""
🔍 PROVABLY FAIR INDEPENDENT VERIFIER (Python)
-----------------------------------------------
Verifies any roll cryptographically offline using HMAC-SHA256.
Formula:
  hash = HMAC_SHA256(key=server_seed, message="client_seed:nonce")
  int_val = parseInt(hash[0:8], 16)
  roll = int_val % 1000
"""

import hmac
import hashlib
import sys

def verify_roll(server_seed: str, client_seed: str, nonce: int):
    message = f"{client_seed}:{nonce}".encode('utf-8')
    key = server_seed.encode('utf-8')
    hmac_hash = hmac.new(key, message, hashlib.sha256).hexdigest()
    
    sub_hex = hmac_hash[:8]
    int_val = int(sub_hex, 16)
    roll = int_val % 1000
    is_jackpot = (roll == 777)
    
    print("\n=======================================================")
    print("       🔬 RESULTADO DE AUDITORÍA CRIPTOGRÁFICA         ")
    print("=======================================================")
    print(f"- Server Seed : {server_seed}")
    print(f"- Client Seed : {client_seed}")
    print(f"- Nonce       : {nonce}")
    print(f"- HMAC Hash   : {hmac_hash}")
    print(f"- 32-bit Hex  : {sub_hex} -> Decimal: {int_val}")
    print(f"- Roll Final  : {roll} ({'🏆 JACKPOT HIT (777)!' if is_jackpot else 'Sin Jackpot'})")
    print("=======================================================\n")
    return roll

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python verify_fairness.py <server_seed> <client_seed> <nonce>")
        print("Ejemplo: python verify_fairness.py 9f82ab... seed_user_1 1")
        sys.exit(1)
        
    server_seed = sys.argv[1]
    client_seed = sys.argv[2]
    nonce = int(sys.argv[3])
    verify_roll(server_seed, client_seed, nonce)
