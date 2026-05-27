"""
daily_credit.py - Injection journaliere de USD dans le portefeuille
Ajoute automatiquement une somme fixe en USD chaque jour.
Usage: python daily_credit.py [montant_usd]
Defaut: 100 USD par jour
"""

import os
import sys
import json
from datetime import datetime, timedelta

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_FILE = os.path.join(SCRIPT_DIR, "wallet.json")
CREDIT_LOG = os.path.join(SCRIPT_DIR, "credit_log.json")
AUDIO_DIR  = os.path.join(SCRIPT_DIR, "audio_logs")

# Montant journalier par defaut en USD
DEFAULT_DAILY_AMOUNT = 100.0

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        return {"USD": 0.0, "BTC": 0.0, "ETH": 0.0, "SOL": 0.0, "USDT": 0.0}
    with open(WALLET_FILE, "r") as f:
        return json.load(f)

def save_wallet(wallet):
    with open(WALLET_FILE, "w") as f:
        json.dump(wallet, f, indent=2)

def load_credit_log():
    if os.path.exists(CREDIT_LOG):
        with open(CREDIT_LOG, "r") as f:
            return json.load(f)
    return {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "daily_amount_usd": DEFAULT_DAILY_AMOUNT,
        "total_credited_usd": 0.0,
        "next_credit_due": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "entries": []
    }

def save_credit_log(log):
    with open(CREDIT_LOG, "w") as f:
        json.dump(log, f, indent=2)

def generate_audio_credit(amount, total):
    """Synthese vocale de la confirmation de credit journalier."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    try:
        from gtts import gTTS
        import subprocess, threading
        now_str = datetime.now().strftime("%d %B %Y")
        text = (
            f"Credit journalier effectue le {now_str}. "
            f"Montant credite : {amount:.2f} dollars americains. "
            f"Solde USD total cumule injecte : {total:.2f} dollars."
        )
        audio_file = os.path.join(AUDIO_DIR, "latest_credit.mp3")
        tts = gTTS(text=text, lang="fr", slow=False)
        tts.save(audio_file)

        # Lecture asynchrone via Windows Media Player
        def _play():
            ps = (
                f"$p=New-Object -ComObject WMPlayer.OCX;"
                f"$p.URL='{audio_file}';"
                f"$p.controls.play();"
                f"while($p.playState -ne 1){{Start-Sleep -Milliseconds 100}}"
            )
            subprocess.run(["powershell", "-Command", ps],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        threading.Thread(target=_play, daemon=True).start()
        return True
    except Exception as e:
        print(f"[Audio] Impossible de generer l audio : {e}")
        return False

def inject_daily_credit(amount_usd=None):
    now = datetime.now()
    log = load_credit_log()

    # Montant configurable via argument ou log
    if amount_usd is None:
        amount_usd = log.get("daily_amount_usd", DEFAULT_DAILY_AMOUNT)

    # Verifier si le credit est deja passe pour aujourd'hui
    entries_today = [
        e for e in log["entries"]
        if e["date"].startswith(now.strftime("%Y-%m-%d"))
    ]
    if entries_today:
        print(f"[Info] Credit deja effectue aujourd hui le {now.strftime('%Y-%m-%d')}.")
        print(f"       Prochain credit : {log.get('next_credit_due','N/A')}")
        return False

    # Charger et mettre a jour le portefeuille
    wallet = load_wallet()
    before = wallet.get("USD", 0.0)
    wallet["USD"] = before + amount_usd
    save_wallet(wallet)

    # Calculer prochaine echeance
    next_due = (now + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

    # Mettre a jour le journal de credits
    log["total_credited_usd"] += amount_usd
    log["next_credit_due"] = next_due
    log["daily_amount_usd"] = amount_usd
    log["entries"].append({
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "amount_usd": amount_usd,
        "balance_before": before,
        "balance_after": wallet["USD"],
        "next_credit_due": next_due
    })
    save_credit_log(log)

    # Affichage console
    print()
    print("=" * 58)
    print("  💳 INJECTION JOURNALIERE USD - PORTEFEUILLE CRYPTO")
    print("=" * 58)
    print(f"  Date              : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Montant cred.     : +${amount_usd:.2f} USD")
    print(f"  Solde avant       : ${before:.2f} USD")
    print(f"  Solde apres       : ${wallet['USD']:.2f} USD")
    print(f"  Total cumule inj. : ${log['total_credited_usd']:.2f} USD")
    print(f"  Prochain credit   : {next_due}")
    print("=" * 58)

    # Synthese vocale
    generate_audio_credit(amount_usd, log["total_credited_usd"])

    return True

if __name__ == "__main__":
    amount = DEFAULT_DAILY_AMOUNT
    if len(sys.argv) > 1:
        try:
            amount = float(sys.argv[1])
        except ValueError:
            print(f"Montant invalide. Utilisation du defaut : ${DEFAULT_DAILY_AMOUNT}")

    inject_daily_credit(amount)
