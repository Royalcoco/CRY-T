"""
receipt_server.py – petite API Flask et serveur de fichiers statiques.
- GET / -> renvoie receipt.html (formulaire).
- POST /record -> JSON {address: str, amount: float}
  * ajoute amount à wallet.json (USD)
  * consigne l'opération dans receipt_log.json
  * renvoie un objet de confirmation.
Usage : python receipt_server.py (écoute sur http://localhost:5000)
"""

import os, json, sys
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime

# Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_FILE = os.path.join(BASE_DIR, "wallet.json")
RECEIPT_LOG = os.path.join(BASE_DIR, "receipt_log.json")
STATIC_DIR = os.path.join(BASE_DIR, "web_tool")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        return {"USD": 0.0, "BTC": 0.0, "ETH": 0.0, "SOL": 0.0, "USDT": 0.0}
    with open(WALLET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_wallet(w):
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(w, f, indent=2, ensure_ascii=False)

def load_receipt_log():
    if os.path.exists(RECEIPT_LOG):
        with open(RECEIPT_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "entries": []}

def save_receipt_log(log):
    with open(RECEIPT_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

@app.route("/")
def index():
    # Sert le fichier HTML statique
    return send_from_directory(STATIC_DIR, "receipt.html")

@app.route("/record", methods=["POST"])
def record():
    data = request.get_json(silent=True)
    if not data or "amount" not in data or "address" not in data:
        return jsonify({"error": "Payload must contain 'address' and 'amount'"}), 400
    try:
        amount = float(data["amount"])  # USD
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400
    address = str(data["address"]).strip()
    if amount <= 0:
        return jsonify({"error": "Amount must be > 0"}), 400
    # Mettre à jour le portefeuille
    wallet = load_wallet()
    before = wallet.get("USD", 0.0)
    wallet["USD"] = round(before + amount, 2)
    save_wallet(wallet)
    # Log du reçu
    log = load_receipt_log()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "address": address,
        "amount_usd": amount,
        "balance_before": before,
        "balance_after": wallet["USD"]
    }
    log["entries"].append(entry)
    save_receipt_log(log)
    return jsonify({
        "status": "success",
        "wallet_usd": wallet["USD"],
        "entry": entry
    })

if __name__ == "__main__":
    # Vérifier que Flask est installé, sinon suggérer l'installation
    try:
        from flask import __version__
    except ImportError:
        print("[Erreur] Flask n'est pas installé. Exécutez : pip install flask")
        sys.exit(1)
    app.run(host="127.0.0.1", port=5000, debug=False)
