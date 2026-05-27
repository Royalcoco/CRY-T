"""
withdraw_payment.py - Retirer une somme USD du portefeuille et enregistrer la transaction.
Usage: python withdraw_payment.py <montant_usd>
"""

import os
import sys
import json
from datetime import datetime

# Ensure UTF-8 on Windows consoles
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_FILE = os.path.join(SCRIPT_DIR, "wallet.json")
PAYMENT_LOG = os.path.join(SCRIPT_DIR, "payment_log.json")

DEFAULT_WITHDRAW_AMOUNT = 10.0  # USD, used when no argument supplied

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        return {"USD": 0.0, "BTC": 0.0, "ETH": 0.0, "SOL": 0.0, "USDT": 0.0}
    with open(WALLET_FILE, "r", encoding='utf-8') as f:
        return json.load(f)

def save_wallet(wallet):
    with open(WALLET_FILE, "w", encoding='utf-8') as f:
        json.dump(wallet, f, indent=2)

def load_payment_log():
    if os.path.exists(PAYMENT_LOG):
        with open(PAYMENT_LOG, "r", encoding='utf-8') as f:
            return json.load(f)
    return {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_withdrawn_usd": 0.0,
        "entries": []
    }

def save_payment_log(log):
    with open(PAYMENT_LOG, "w", encoding='utf-8') as f:
        json.dump(log, f, indent=2)

def withdraw_usd(amount_usd):
    wallet = load_wallet()
    balance = wallet.get("USD", 0.0)
    if amount_usd > balance:
        print(f"[Erreur] Fonds insuffisants: solde USD {balance:.2f}, montant demandé {amount_usd:.2f}")
        return False
    wallet["USD"] = round(balance - amount_usd, 2)
    save_wallet(wallet)

    log = load_payment_log()
    log["total_withdrawn_usd"] = round(log.get("total_withdrawn_usd", 0.0) + amount_usd, 2)
    log["entries"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amount_usd": amount_usd,
        "balance_after": wallet["USD"]
    })
    save_payment_log(log)

    print("=" * 58)
    print("   💸 RETRAIT USD – PORTFOLIO")
    print("=" * 58)
    print(f"   Date               : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Montant retiré     : -${amount_usd:.2f} USD")
    print(f"   Solde après retrait: ${wallet['USD']:.2f} USD")
    print(f"   Total retiré cumulé: ${log['total_withdrawn_usd']:.2f} USD")
    print("=" * 58)
    return True

if __name__ == "__main__":
    amount = DEFAULT_WITHDRAW_AMOUNT
    if len(sys.argv) > 1:
        try:
            amount = float(sys.argv[1])
        except ValueError:
            print(f"Montant invalide, utilisation du défaut {DEFAULT_WITHDRAW_AMOUNT} USD")
    withdraw_usd(amount)
