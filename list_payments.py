"""
list_payments.py - Affiche l'historique des retraits monétaires enregistrés.
Usage: python list_payments.py
"""
import os, json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PAYMENT_LOG = os.path.join(SCRIPT_DIR, "payment_log.json")

def load_log():
    if not os.path.exists(PAYMENT_LOG):
        print("[Info] Aucun log de paiement trouvé.")
        return None
    with open(PAYMENT_LOG, "r", encoding='utf-8') as f:
        return json.load(f)

def display(log):
    entries = log.get("entries", [])
    if not entries:
        print("[Info] Aucun retrait enregistré.")
        return
    print("="*60)
    print(" Historique des retraits monétaires ".center(60))
    print("="*60)
    print(f"{'Date':20} | {'Montant USD':12} | {'Solde après':12}")
    print("-"*60)
    for e in entries:
        date = e.get('date','')[:19]
        amt = f"${e.get('amount_usd',0):.2f}"
        bal = f"${e.get('balance_after',0):.2f}"
        print(f"{date:20} | {amt:12} | {bal:12}")
    print("="*60)
    print(f"Total cumulé retiré : ${log.get('total_withdrawn_usd',0):.2f} USD")

if __name__ == '__main__':
    log = load_log()
    if log:
        display(log)
