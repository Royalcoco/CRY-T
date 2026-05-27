import os, json, sys
from flask import Flask, request, jsonify, send_from_directory, abort
from datetime import datetime
import requests

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_FILE = os.path.join(BASE_DIR, "wallet.json")
EXPORT_LOG = os.path.join(BASE_DIR, "export_log.json")
TOKEN_LOG = os.path.join(BASE_DIR, "token_log.json")
STATIC_DIR = os.path.join(BASE_DIR, "web_tool")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")

# -------------------- Helper Functions --------------------

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        return {"USD": 0.0, "BTC": 0.0, "ETH": 0.0, "SOL": 0.0, "USDT": 0.0}
    with open(WALLET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_wallet(w):
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(w, f, indent=2, ensure_ascii=False)

def load_export_log():
    if os.path.exists(EXPORT_LOG):
        with open(EXPORT_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "entries": []}

def save_export_log(log):
    with open(EXPORT_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

def load_token_log():
    if os.path.exists(TOKEN_LOG):
        with open(TOKEN_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "entries": []}

def save_token_log(log):
    with open(TOKEN_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

def fetch_price(symbol):
    """Fetch current USD price for a crypto symbol using CoinGecko.
    Symbol should be lower‑case (e.g., 'btc', 'eth')."""
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": symbol, "vs_currencies": "usd"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get(symbol, {}).get('usd')
    except Exception:
        return None

# -------------------- Routes --------------------
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "receipt.html")

@app.route("/wallet")
def wallet_page():
    return send_from_directory(STATIC_DIR, "wallet.html")

@app.route("/wallet_data", methods=["GET"])
def wallet_data():
    return jsonify(load_wallet())

# Existing export endpoint (renamed to /export_cash for clarity)
@app.route("/export_cash", methods=["POST"])
def export_cash():
    data = request.get_json(silent=True)
    if not data or "amount" not in data:
        return jsonify({"error": "Payload must contain 'amount' (USD)"}), 400
    try:
        amount = float(data["amount"])  # USD to export
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount value"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be > 0"}), 400
    wallet = load_wallet()
    available = wallet.get("USD", 0.0)
    if amount > available:
        return jsonify({"error": f"Insufficient funds: {available:.2f} USD available"}), 400
    before = available
    wallet["USD"] = round(available - amount, 2)
    save_wallet(wallet)
    log = load_export_log()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amount_usd": amount,
        "balance_before": before,
        "balance_after": wallet["USD"],
        "description": data.get("description", "Export cash as commercial command")
    }
    log["entries"].append(entry)
    save_export_log(log)
    return jsonify({"status": "success", "wallet_usd": wallet["USD"], "export_entry": entry})

# New token purchase / sell endpoint
@app.route("/tokenize", methods=["POST"])
def tokenize():
    data = request.get_json(silent=True)
    required = {"symbol", "amount", "side"}
    if not data or not required.issubset(data):
        return jsonify({"error": f"Payload must contain {required}"}), 400
    symbol = data["symbol"].lower()
    try:
        amount = float(data["amount"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400
    side = data["side"].lower()
    if side not in ["buy", "sell"]:
        return jsonify({"error": "side must be 'buy' or 'sell'"}), 400
    price_usd = fetch_price(symbol)
    if price_usd is None:
        return jsonify({"error": f"Could not fetch price for {symbol}"}), 502
    usd_value = round(price_usd * amount, 2)
    wallet = load_wallet()
    # Update token balance
    token_key = symbol.upper()
    wallet[token_key] = wallet.get(token_key, 0.0) + (amount if side == "buy" else -amount)
    # Update USD balance accordingly
    if side == "buy":
        if wallet["USD"] < usd_value:
            return jsonify({"error": f"Insufficient USD balance ({wallet["USD"]}) for purchase"}), 400
        wallet["USD"] = round(wallet["USD"] - usd_value, 2)
    else:
        wallet["USD"] = round(wallet["USD"] + usd_value, 2)
    save_wallet(wallet)
    # Log token transaction
    log = load_token_log()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": token_key,
        "side": side,
        "amount": amount,
        "price_usd": price_usd,
        "usd_value": usd_value,
        "wallet_usd_after": wallet["USD"],
        "wallet_token_balance": wallet[token_key]
    }
    log["entries"].append(entry)
    save_token_log(log)
    return jsonify({"status": "success", "entry": entry})

# Health check
@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    try:
        from flask import __version__
    except ImportError:
        print("[Erreur] Flask n'est pas installé. Exécutez : pip install flask")
        sys.exit(1)
    # Run on port 5001 to avoid clash with receipt_server
    app.run(host="127.0.0.1", port=5001, debug=False)
from flask import Flask, request, jsonify, send_from_directory, safe_join, abort

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_FILE = os.path.join(BASE_DIR, "wallet.json")
EXPORT_LOG = os.path.join(BASE_DIR, "export_log.json")
STATIC_DIR = os.path.join(BASE_DIR, "web_tool")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")

# Serve wallet view page
@app.route("/wallet")
def wallet_page():
    return send_from_directory(STATIC_DIR, "wallet.html")

# JSON API for wallet data
@app.route("/wallet_data", methods=["GET"])
def wallet_data():
    return jsonify(load_wallet())

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        return {"USD": 0.0, "BTC": 0.0, "ETH": 0.0, "SOL": 0.0, "USDT": 0.0}
    with open(WALLET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_wallet(w):
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(w, f, indent=2, ensure_ascii=False)

def load_export_log():
    if os.path.exists(EXPORT_LOG):
        with open(EXPORT_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "entries": []}

def save_export_log(log):
    with open(EXPORT_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

@app.route("/export", methods=["POST"]) 
def export_cash():
    data = request.get_json(silent=True)
    if not data or "amount" not in data:
        return jsonify({"error": "Payload must contain 'amount' (USD)"}), 400
    try:
        amount = float(data["amount"])  # USD to export
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount value"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be > 0"}), 400

    wallet = load_wallet()
    available = wallet.get("USD", 0.0)
    if amount > available:
        return jsonify({"error": f"Insufficient funds: {available:.2f} USD available"}), 400

    # Deduct amount
    before = available
    wallet["USD"] = round(available - amount, 2)
    save_wallet(wallet)

    # Log export
    log = load_export_log()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amount_usd": amount,
        "balance_before": before,
        "balance_after": wallet["USD"],
        "description": data.get("description", "Export cash as commercial command")
    }
    log["entries"].append(entry)
    save_export_log(log)
    return jsonify({
        "status": "success",
        "wallet_usd": wallet["USD"],
        "export_entry": entry
    })

if __name__ == "__main__":
    # Ensure Flask is installed
    try:
        from flask import __version__
    except ImportError:
        print("[Erreur] Flask n'est pas installé. Exécutez : pip install flask")
        sys.exit(1)
    # Run on a different port to avoid clash with receipt_server
    app.run(host="127.0.0.1", port=5001, debug=False)
