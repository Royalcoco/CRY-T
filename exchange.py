import os
import json
import uuid
from datetime import datetime
import requests

WALLET_FILE = os.path.join(os.path.dirname(__file__), "wallet.json")

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "USDT": "tether"
}

# Fallback/mock prices in USD if API is offline
MOCK_PRICES = {
    "USD": 1.0,
    "USDT": 1.0,
    "BTC": 65000.0,
    "ETH": 35000.0,
    "SOL": 150.0
}

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        default_wallet = {
            "USD": 10000.0,
            "BTC": 0.0,
            "ETH": 0.0,
            "SOL": 0.0,
            "USDT": 0.0
        }
        save_wallet(default_wallet)
        return default_wallet
    with open(WALLET_FILE, "r") as f:
        return json.load(f)

def save_wallet(wallet):
    with open(WALLET_FILE, "w") as f:
        json.dump(wallet, f, indent=2)

def get_crypto_prices():
    """Fetch live prices from CoinGecko or fallback to mock prices if offline."""
    prices = {"USD": 1.0}
    
    ids_param = ",".join(COINGECKO_IDS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd"
    
    try:
        # 3 seconds timeout to prevent freezing the CLI
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            for symbol, cg_id in COINGECKO_IDS.items():
                if cg_id in data:
                    prices[symbol] = float(data[cg_id]["usd"])
            # Ensure USDT is pegged closely to 1.0 if not fetched
            if "USDT" not in prices:
                prices["USDT"] = 1.0
            return prices, True
    except Exception:
        pass
    
    # Return fallback prices if request fails
    return MOCK_PRICES.copy(), False

def swap_tokens(from_token, to_token, amount):
    """
    Perform token swap.
    Returns (success_bool, receipt_dict, error_msg)
    """
    wallet = load_wallet()
    prices, is_live = get_crypto_prices()
    
    from_token = from_token.upper()
    to_token = to_token.upper()
    
    if from_token not in wallet:
        return False, None, f"Token d'origine '{from_token}' invalide."
    if to_token not in wallet:
        return False, None, f"Token de destination '{to_token}' invalide."
    
    if wallet[from_token] < amount:
        return False, None, f"Solde insuffisant en {from_token}. Solde disponible : {wallet[from_token]}."
    
    if amount <= 0:
        return False, None, "Le montant doit être strictement supérieur à 0."
        
    # Calculate swap amount
    # Price of 1 from_token in USD
    price_from_usd = prices[from_token]
    # Price of 1 to_token in USD
    price_to_usd = prices[to_token]
    
    # Amount of to_token received
    received_amount = (amount * price_from_usd) / price_to_usd
    rate = price_from_usd / price_to_usd
    
    # Update wallet balances
    wallet[from_token] -= amount
    wallet[to_token] += received_amount
    save_wallet(wallet)
    
    # Generate receipt form
    receipt = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "from_token": from_token,
        "from_amount": amount,
        "to_token": to_token,
        "to_amount": received_amount,
        "rate": rate,
        "is_live_price": is_live,
        "status": "SUCCESS"
    }
    
    return True, receipt, None
