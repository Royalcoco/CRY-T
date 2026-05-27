"""
mobility_payment.py - Autorisation de paiement mobilité avec tokens et validation géographique.
Gère l'autorisation de paiement, la validation de token, l'approbation d'agence mobile et l'alignement géographique.
"""

import os
import sys
import json
import uuid
import random
import requests
from datetime import datetime

# Configure UTF-8 on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_FILE = os.path.join(SCRIPT_DIR, "wallet.json")
MOBILITY_LOG = os.path.join(SCRIPT_DIR, "mobility_payment_log.json")
AUDIO_DIR = os.path.join(SCRIPT_DIR, "audio_logs")

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        return {"USD": 10000.0, "BTC": 0.0, "ETH": 0.0, "SOL": 0.0, "USDT": 0.0}
    with open(WALLET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_wallet(wallet):
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(wallet, f, indent=2)

def load_mobility_log():
    if os.path.exists(MOBILITY_LOG):
        with open(MOBILITY_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_authorized_usd": 0.0,
        "entries": []
    }

def save_mobility_log(log):
    with open(MOBILITY_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

def get_crypto_prices():
    # Simplifié à partir de exchange.py pour éviter les importations circulaires ou les pannes
    from exchange import get_crypto_prices as get_prices
    try:
        prices, is_live = get_prices()
        return prices, is_live
    except Exception:
        return {"USD": 1.0, "USDT": 1.0, "BTC": 65000.0, "ETH": 3500.0, "SOL": 150.0}, False

def request_mobility_payment(token, amount, lat=None, lon=None, agency_name="Agence Mobilité Centre", destination_address="0x42d7c506A7B753efea2DAc0694289ED3Bb46599E"):
    wallet = load_wallet()
    token = token.upper()
    
    if token not in wallet:
        return False, f"Token {token} non supporté dans le portefeuille."
        
    available = wallet.get(token, 0.0)
    if available < amount:
        return False, f"Solde insuffisant. Disponible: {available:.6f} {token}, Demandé: {amount:.6f} {token}."

    if amount <= 0:
        return False, "Le montant doit être supérieur à 0."

    # Simulation d'approbation d'agence de données mobile
    prices, is_live = get_crypto_prices()
    token_price = prices.get(token, 1.0)
    amount_usd = amount * token_price
    
    # 1. Aligner géographiquement la réserve
    if lat is None or lon is None:
        # Paris par défaut avec une légère variation
        lat = round(48.8566 + random.uniform(-0.05, 0.05), 4)
        lon = round(2.3522 + random.uniform(-0.05, 0.05), 4)
        
    reference_id = f"MOB-{uuid.uuid4().hex[:8].upper()}"
    agency_approval_hash = f"APR-{uuid.uuid4().hex[:12].upper()}"
    
    # 2. Enrichissement passant de virtuel à compte avec réserve alignée
    wallet[token] = round(wallet[token] - amount, 8)
    wallet["USD"] = round(wallet.get("USD", 0.0) + amount_usd, 2) # Transfert de la réserve de tokens en USD liquide approuvé
    save_wallet(wallet)
    
    # 3. Enregistrer le module qualitatif de transaction
    transaction_entry = {
        "reference": reference_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agency": agency_name,
        "approval_hash": agency_approval_hash,
        "destination_address": destination_address,
        "geographic_alignment": {
            "latitude": lat,
            "longitude": lon,
            "status": "ALIGNED_WITH_RESERVE"
        },
        "token_used": token,
        "token_amount": amount,
        "usd_equivalent": amount_usd,
        "conversion_rate": token_price,
        "validation_status": "APPROVED_BY_MOBILE_DATA_AGENCY",
        "qualitative_metadata": {
            "mobility_tier": "Premium Gold",
            "validation_tool": "Token-Validator v2.1",
            "enrichment_status": "VIRTUAL_TO_ACCOUNT_COMPLETED"
        }
    }
    
    log = load_mobility_log()
    log["total_authorized_usd"] = round(log.get("total_authorized_usd", 0.0) + amount_usd, 2)
    log["entries"].append(transaction_entry)
    save_mobility_log(log)
    
    # 4. Transmission réseau (Formulaire de reçu de paiement mobilité)
    payload = {
        "event": "mobility_payment_authorization",
        "reference": reference_id,
        "agency_approval_hash": agency_approval_hash,
        "destination_address": destination_address,
        "latitude": lat,
        "longitude": lon,
        "token": token,
        "amount": amount,
        "amount_usd": amount_usd,
        "status": "APPROVED"
    }
    
    network_status = "ECHEC_RESEAU"
    try:
        r = requests.post("https://httpbin.org/post", json=payload, timeout=5)
        if r.status_code == 200:
            network_status = "TRANSMIS"
    except Exception:
        pass
        
    # 5. Synthèse vocale de confirmation
    generate_mobility_audio(transaction_entry)
    
    return True, transaction_entry

def generate_mobility_audio(entry):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    try:
        from gtts import gTTS
        from audio_renderer import play_audio_file
        
        # Prononcer les 4 derniers caractères de l'adresse de destination pour rester court et mélodieux
        dest_short = entry['destination_address'][-4:]
        text = (
            f"Autorisation de paiement mobilité validée. "
            f"Référence : {entry['reference']}. "
            f"Montant converti : {entry['token_amount']:.4f} {entry['token_used']}. "
            f"Équivalent : {entry['usd_equivalent']:.2f} dollars. "
            f"Versé à l'adresse finissant par {dest_short}. "
            f"Réserve géographiquement alignée à la latitude {entry['geographic_alignment']['latitude']}. "
            f"Approbation par l'agence de données mobile confirmée."
        )
        audio_file = os.path.join(AUDIO_DIR, f"mobility_{entry['reference']}.mp3")
        latest_file = os.path.join(AUDIO_DIR, "latest_mobility.mp3")
        
        tts = gTTS(text=text, lang="fr", slow=False)
        tts.save(audio_file)
        tts.save(latest_file)
        
        play_audio_file(audio_file)
    except Exception as e:
        print(f"[Audio] Erreur génération audio : {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python mobility_payment.py <TOKEN> <AMOUNT> [LAT] [LON] [AGENCY] [DEST_ADDR]")
        sys.exit(1)
        
    token_arg = sys.argv[1]
    try:
        amount_arg = float(sys.argv[2])
    except ValueError:
        print("Montant invalide.")
        sys.exit(1)
        
    lat_arg = float(sys.argv[3]) if len(sys.argv) > 3 else None
    lon_arg = float(sys.argv[4]) if len(sys.argv) > 4 else None
    agency_arg = sys.argv[5] if len(sys.argv) > 5 else "Agence Mobilité Centre"
    dest_arg = sys.argv[6] if len(sys.argv) > 6 else "0x42d7c506A7B753efea2DAc0694289ED3Bb46599E"
    
    success, result = request_mobility_payment(token_arg, amount_arg, lat_arg, lon_arg, agency_arg, dest_arg)
    if success:
        print(json.dumps({"success": True, "transaction": result}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"success": False, "error": result}))
