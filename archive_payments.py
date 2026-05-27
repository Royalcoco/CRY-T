"""
archive_payments.py - Extrait les 4 dernières entrées du journal de paiement et les archive.
Usage: python archive_payments.py [output_dir]
Par défaut, crée un sous‑dossier 'archive' contenant archive_4x3.json & archive_4x3.csv.
"""
import os, json, csv, sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PAYMENT_LOG = os.path.join(SCRIPT_DIR, "payment_log.json")
DEFAULT_OUTDIR = os.path.join(SCRIPT_DIR, "archive")

def load_log():
    if not os.path.exists(PAYMENT_LOG):
        print("[Erreur] payment_log.json introuvable.")
        sys.exit(1)
    with open(PAYMENT_LOG, "r", encoding='utf-8') as f:
        return json.load(f)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def save_json(data, path):
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_csv(entries, path):
    with open(path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Montant USD", "Solde après"])
        for e in entries:
            writer.writerow([
                e.get("date", ""),
                f"${e.get('amount_usd',0):.2f}",
                f"${e.get('balance_after',0):.2f}"
            ])

def main(out_dir=None):
    log = load_log()
    entries = log.get("entries", [])
    # garder les 4 dernières entrées (ou moins si pas assez)
    last_four = entries[-4:]
    if not last_four:
        print("[Info] Aucun retrait à archiver.")
        return
    out_dir = out_dir or DEFAULT_OUTDIR
    ensure_dir(out_dir)
    json_path = os.path.join(out_dir, "archive_4x3.json")
    csv_path = os.path.join(out_dir, "archive_4x3.csv")
    save_json({"archived_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "entries": last_four}, json_path)
    save_csv(last_four, csv_path)
    print(f"✅ Archive créée : {json_path}")
    print(f"✅ CSV créé    : {csv_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    main(out)
