"""
daily_dca.py - Récupération en dose égale journalière de la valeur du portefeuille
Stratégie : DCA (Dollar-Cost Averaging) inversé
- Calcule la valeur totale du portefeuille en USD
- Vend une portion égale journalière de chaque actif crypto vers USD
- Sauvegarde un journal de récolte journalier
- Génère un reçu audio MP3 en français
"""

import os
import sys
import json
import math
from datetime import datetime

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from exchange import load_wallet, save_wallet, get_crypto_prices, swap_tokens
from audio_renderer import generate_receipt_audio, play_audio_file, AUDIO_DIR

HARVEST_LOG = os.path.join(os.path.dirname(__file__), "harvest_log.json")
TOTAL_DAYS = 30  # Récupérer la valeur sur 30 jours en doses égales

def load_harvest_log():
    if os.path.exists(HARVEST_LOG):
        with open(HARVEST_LOG, "r") as f:
            return json.load(f)
    return {
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "total_days": TOTAL_DAYS,
        "day_number": 0,
        "total_harvested_usd": 0.0,
        "days": []
    }

def save_harvest_log(log):
    with open(HARVEST_LOG, "w") as f:
        json.dump(log, f, indent=2)

def calculate_portfolio_value_usd(wallet, prices):
    total = 0.0
    breakdown = {}
    for token, amount in wallet.items():
        price = prices.get(token, 1.0)
        value = amount * price
        breakdown[token] = {
            "amount": amount,
            "price_usd": price,
            "value_usd": value
        }
        total += value
    return total, breakdown

def execute_daily_harvest(dry_run=False):
    """
    Exécute la récolte journalière :
    Vend 1/N de chaque actif crypto pour récupérer en USD en doses égales.
    """
    now = datetime.now()
    wallet = load_wallet()
    prices, is_live = get_crypto_prices()

    total_value_usd, breakdown = calculate_portfolio_value_usd(wallet, prices)
    log = load_harvest_log()

    log["day_number"] += 1
    days_remaining = max(1, TOTAL_DAYS - log["day_number"] + 1)

    print("\n" + "=" * 60)
    print("  📅 DOSE JOURNALIÈRE - RÉCUPÉRATION DU PORTEFEUILLE")
    print("=" * 60)
    print(f"  Date         : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Jour         : {log['day_number']} / {TOTAL_DAYS}")
    print(f"  Jours restants : {days_remaining}")
    print(f"  Valeur totale portefeuille : ${total_value_usd:.2f} USD")
    print("-" * 60)

    # Valeur cible à récupérer aujourd'hui (dose égale)
    daily_target_usd = total_value_usd / days_remaining
    print(f"  💰 Dose à récupérer aujourd'hui : ${daily_target_usd:.2f} USD")
    print("-" * 60)

    receipts = []
    day_harvested = 0.0
    tokens_to_sell = ["BTC", "ETH", "SOL", "USDT"]

    # Répartir la dose égale proportionnellement sur chaque token
    # Pour chaque token : vendre (portion du token représentant daily_target_usd / total_value)
    for token in tokens_to_sell:
        token_data = breakdown.get(token)
        if not token_data or token_data["amount"] <= 0:
            continue

        token_value_usd = token_data["value_usd"]
        if token_value_usd <= 0:
            continue

        # Proportion de ce token dans le portefeuille
        proportion = token_value_usd / total_value_usd if total_value_usd > 0 else 0
        # Montant USD à récolter de ce token aujourd'hui
        token_daily_harvest_usd = daily_target_usd * proportion
        # Montant en token correspondant
        token_amount_to_sell = token_daily_harvest_usd / token_data["price_usd"]

        # Vérification : ne pas vendre plus que disponible
        token_amount_to_sell = min(token_amount_to_sell, token_data["amount"])

        if token_amount_to_sell < 0.000001:
            continue

        print(f"  Vente de {token_amount_to_sell:.6f} {token} (≈ ${token_daily_harvest_usd:.2f} USD)")

        if not dry_run:
            success, receipt, err = swap_tokens(token, "USD", token_amount_to_sell)
            if success:
                day_harvested += receipt["to_amount"]
                receipts.append(receipt)
                print(f"    ✅ Récupéré : ${receipt['to_amount']:.2f} USD")
            else:
                print(f"    ❌ Échec : {err}")
        else:
            day_harvested += token_daily_harvest_usd
            print(f"    [Simulation] Récupération prévue : ${token_daily_harvest_usd:.2f} USD")

    print("-" * 60)
    print(f"  💵 Total récupéré aujourd'hui : ${day_harvested:.2f} USD")

    # Mettre à jour le journal
    log["total_harvested_usd"] += day_harvested
    log["days"].append({
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "day": log["day_number"],
        "harvested_usd": day_harvested,
        "portfolio_value_before": total_value_usd,
        "receipts": [r["id"] for r in receipts]
    })
    save_harvest_log(log)

    print(f"  📊 Total cumulé récupéré : ${log['total_harvested_usd']:.2f} USD")
    print("=" * 60)

    # Générer un résumé audio pour la récolte du jour
    if receipts and not dry_run:
        # Générer un reçu consolidé pour l'audio
        from audio_renderer import ensure_audio_dir
        from gtts import gTTS
        import os as _os
        ensure_audio_dir()
        
        text = (
            f"Dose journalière numéro {log['day_number']} sur {TOTAL_DAYS}. "
            f"Vous avez récupéré {day_harvested:.2f} dollars américains aujourd'hui. "
            f"Votre total cumulé est de {log['total_harvested_usd']:.2f} dollars."
        )
        audio_path = _os.path.join(AUDIO_DIR, f"harvest_day_{log['day_number']}.mp3")
        latest_path = _os.path.join(AUDIO_DIR, "latest_harvest.mp3")
        try:
            tts = gTTS(text=text, lang="fr", slow=False)
            tts.save(audio_path)
            tts.save(latest_path)
            play_audio_file(audio_path)
            print(f"  🔊 Lecture audio du résumé journalier...")
        except Exception as e:
            print(f"  [Avis] Impossible de générer l'audio : {e}")

    return day_harvested, log

if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("[Mode Simulation - Aucune transaction réelle]")
    execute_daily_harvest(dry_run=dry_run)
