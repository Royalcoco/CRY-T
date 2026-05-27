"""
cli.py - CRYPTO LOBBY WALLET & AUDIO SYSTEM
Option [5] : Autorisation de paiement mobilité connectée à l'adresse 0x42d7c506A7B753efea2DAc0694289ED3Bb46599E

== MAP COMMIT / INFORMATIONS REÇUES & ÉCHANGÉES ==
- C-08 : Création du module d'autorisation de paiement mobilité (mobility_payment.py).
- C-09 : Intégration de l'Option [5] de paiement mobilité dans le Lobby (cli.py).
- C-10 : Connexion du versement mobilité à l'adresse de destination 0x42d7c506A7B753efea2DAc0694289ED3Bb46599E.
"""

import os
import sys
import json
import requests
import time

# Reconfigure stdout and stderr to use UTF-8 on Windows to avoid encoding crashes
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback if reconfigure is not available (older Python versions)
        pass

from exchange import load_wallet, get_crypto_prices, swap_tokens
from audio_renderer import generate_receipt_audio, play_audio_file, AUDIO_DIR

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("\033[95m" + "=" * 60 + "\033[0m")
    print("\033[96m" + "    🚀  CRYPTO LOBBY WALLET & AUDIO SYSTEM (v1.0)  🚀" + "\033[0m")
    print("\033[95m" + "=" * 60 + "\033[0m")

def print_prices(prices, is_live):
    status_str = "\033[92m[EN LIGNE - CoinGecko]\033[0m" if is_live else "\033[91m[HORS LIGNE - Simulation]\033[0m"
    print(f" Taux de change {status_str} :")
    print(f"   • BTC  : \033[93m${prices['BTC']:.2f}\033[0m USD")
    print(f"   • ETH  : \033[93m${prices['ETH']:.2f}\033[0m USD")
    print(f"   • SOL  : \033[93m${prices['SOL']:.2f}\033[0m USD")
    print(f"   • USDT : \033[93m${prices['USDT']:.4f}\033[0m USD")
    print("-" * 60)

def print_balances(wallet, prices):
    print(" 💼 SOLDE DU PORTEFEUILLE (LOBBY) :")
    total_usd = 0.0
    for token, amount in wallet.items():
        price_usd = prices.get(token, 1.0)
        value_usd = amount * price_usd
        total_usd += value_usd
        if amount > 0:
            print(f"   • {token:<5} : \033[97m{amount:>12.6f}\033[0m (\033[90m${value_usd:>10.2f} USD\033[0m)")
        else:
            print(f"   • {token:<5} : \033[90m{amount:>12.6f}\033[0m (\033[90m$0.00 USD\033[0m)")
    print("-" * 60)
    print(f" 💰 Valeur totale estimée : \033[92m${total_usd:.2f} USD\033[0m")
    print("\033[95m" + "=" * 60 + "\033[0m")

def display_receipt_form(receipt):
    print("\n\033[93m" + "┌" + "─" * 58 + "┐")
    print("│                     REÇU D'ÉCHANGE                       │")
    print("├" + "─" * 58 + "┤")
    print(f"│ ID Transaction : {receipt['id']:<39} │")
    print(f"│ Horodatage     : {receipt['timestamp']:<39} │")
    print(f"│ Statut         : \033[92m{receipt['status']:<39}\033[93m │")
    print("├" + "─" * 58 + "┤")
    from_str = f"{receipt['from_amount']:.6f} {receipt['from_token']}"
    to_str = f"{receipt['to_amount']:.6f} {receipt['to_token']}"
    print(f"│ Source         : {from_str:<39} │")
    print(f"│ Destination    : {to_str:<39} │")
    print(f"│ Taux appliqué  : 1 {receipt['from_token']} = {receipt['rate']:.6f} {receipt['to_token']:<15} │")
    print(f"│ Mode Prix      : {'LIVE (CoinGecko)' if receipt['is_live_price'] else 'SIMULÉ / OFFLINE':<39} │")
    print("└" + "─" * 58 + "┘\033[0m")

def send_receipt_network(receipt):
    print("\n\033[90m[Réseau] Envoi du reçu d'échange sous forme de formulaire...\033[0m")
    url = "https://httpbin.org/post"
    
    # We serialize the receipt as a form-like JSON post
    payload = {
        "event": "token_swap_receipt",
        "receipt_id": receipt["id"],
        "timestamp": receipt["timestamp"],
        "from_token": receipt["from_token"],
        "from_amount": receipt["from_amount"],
        "to_token": receipt["to_token"],
        "to_amount": receipt["to_amount"],
        "rate": receipt["rate"],
        "status": receipt["status"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("\033[92m[Réseau] Réponse du serveur (HTTP 200 OK) : Reçu transmis avec succès !\033[0m")
            # Return True to indicate successful network send
            return True
        else:
            print(f"\033[91m[Réseau] Serveur a répondu avec l'erreur HTTP {response.status_code}\033[0m")
    except Exception as e:
        print(f"\033[91m[Réseau] Échec de transmission réseau (Serveur injoignable ou hors-ligne)\033[0m")
    
    return False

def menu_swap():
    wallet = load_wallet()
    print("\n👉 SUPPORTÉ : USD, BTC, ETH, SOL, USDT")
    
    from_token = input("Token d'origine (ex: USD) : ").strip().upper()
    if from_token not in wallet:
        print(f"\033[91mErreur : Le token '{from_token}' n'existe pas dans le wallet.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    to_token = input("Token de destination (ex: BTC) : ").strip().upper()
    if to_token not in wallet:
        print(f"\033[91mErreur : Le token '{to_token}' n'existe pas dans le wallet.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    if from_token == to_token:
        print("\033[91mErreur : Impossible d'échanger un token contre lui-même.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    try:
        amount_input = input(f"Montant de {from_token} à échanger : ").strip()
        amount = float(amount_input)
    except ValueError:
        print("\033[91mErreur : Montant invalide.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    print("\n\033[96m[Système] Traitement de la transaction...\033[0m")
    success, receipt, err = swap_tokens(from_token, to_token, amount)
    
    if not success:
        print(f"\033[91mÉchec : {err}\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    # Print receipt form
    display_receipt_form(receipt)
    
    # Send over network (form-like request)
    send_receipt_network(receipt)
    
    # Generate audio message (saved to audio_logs)
    print("\033[90m[Audio] Synthèse vocale de la transaction...\033[0m")
    audio_path = generate_receipt_audio(receipt)
    if audio_path:
        # Play the generated audio file asynchronously
        play_audio_file(audio_path)
        print("\033[92m[Audio] Lecture audio en cours en arrière-plan...\033[0m")

    input("\nAppuyez sur Entrée pour revenir au Lobby...")

def menu_history():
    if not os.path.exists(AUDIO_DIR):
        print("\nAucun historique d'échange trouvé.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    files = [f for f in os.listdir(AUDIO_DIR) if f.startswith("receipt_") and f.endswith(".mp3")]
    if not files:
        print("\nAucun historique d'échange trouvé.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    print("\n📚 HISTORIQUE DES TRANSACTIONS AUDIO (MP3) :")
    for idx, f in enumerate(files, 1):
        print(f"  [{idx}] {f}")
        
    choice = input("\nEntrez le numéro du fichier audio pour le réécouter (ou Entrée pour quitter) : ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(files):
            filepath = os.path.join(AUDIO_DIR, files[idx])
            print(f"\nLecture de : {files[idx]}...")
            play_audio_file(filepath)
        else:
            print("\033[91mSélection invalide.\033[0m")
            time.sleep(1)

def init_history_if_empty(histories, current_prices):
    import random
    for token, price in current_prices.items():
        if token in histories and not histories[token]:
            # Generate 9 simulated historical prices oscillating slightly
            for _ in range(9):
                oscillation = 1.0 + random.uniform(-0.015, 0.015)
                histories[token].append(price * oscillation)

def draw_scopic_chart(token, history):
    height = 7
    width = 30 # 10 points * 3 spaces
    
    min_val = min(history)
    max_val = max(history)
    
    # Avoid division by zero
    if min_val == max_val:
        min_val -= min_val * 0.01 if min_val != 0 else 1.0
        max_val += max_val * 0.01 if max_val != 0 else 1.0
        
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    # Plot points
    for i, val in enumerate(history):
        col = i * 3
        if col >= width:
            continue
        # Scale to row index (0 to height-1)
        row_idx = int((val - min_val) / (max_val - min_val) * (height - 1))
        row_idx = max(0, min(height - 1, row_idx))
        grid[row_idx][col] = "●"
        
    # Draw chart from top to bottom
    print(f"\n\033[96m=== GRAPHOSCOPE (RENDU SCOPIQUE) : {token} / USD ===\033[0m")
    
    for r in range(height - 1, -1, -1):
        row_val = min_val + (r / (height - 1)) * (max_val - min_val)
        if row_val >= 1000:
            label = f"${row_val:.1f}"
        else:
            label = f"${row_val:.4f}"
            
        row_str = "".join(grid[r])
        print(f"  {label:>10} │ {row_str}")
        
    print("             └" + "─" * width + "►")
    print("               T-9  T-8  T-7  T-6  T-5  T-4  T-3  T-2  T-1  T-Real")
    print("\033[90m(Affiche les oscillations de prix basées sur les réserves de liquidité)\033[0m")

def menu_scopic(price_histories):
    print("\n📈 CHOIX DU TOKEN POUR LE RENDU SCOPIQUE :")
    print(" [1] BTC (Bitcoin)")
    print(" [2] ETH (Ethereum)")
    print(" [3] SOL (Solana)")
    print(" [4] USDT (Tether)")
    
    choice = input("\nChoisissez le token (1-4) : ").strip()
    tokens = {"1": "BTC", "2": "ETH", "3": "SOL", "4": "USDT"}
    
    if choice in tokens:
        token = tokens[choice]
        history = price_histories[token]
        draw_scopic_chart(token, history)
    else:
        print("\033[91mChoix invalide.\033[0m")
    input("\nAppuyez sur Entrée pour revenir au Lobby...")

def draw_mobility_map(lat, lon):
    print("\n\033[93m🗺️ CARTE GÉOGRAPHIQUE DE LA RÉSERVE D'AGENCE :\033[0m")
    grid_size = 11
    import random
    print("  ┌" + "─" * (grid_size * 2 + 1) + "┐")
    for r in range(grid_size):
        row_cells = []
        for c in range(grid_size):
            if r == grid_size // 2 and c == grid_size // 2:
                row_cells.append("\033[91m📍\033[0m") # The coordinate marker
            else:
                val = random.random()
                if val < 0.15:
                    row_cells.append("\033[94m≈\033[0m") # Water
                elif val < 0.25:
                    row_cells.append("\033[92m▲\033[0m") # Mountains/Land
                else:
                    row_cells.append("\033[90m·\033[0m") # Space
        print("  │ " + " ".join(row_cells) + " │")
    print("  └" + "─" * (grid_size * 2 + 1) + "┘")
    print(f"  \033[96mCoordonnées : Lat {lat:.4f}, Lon {lon:.4f} (Réserve alignée géographiquement)\033[0m")

def menu_mobility():
    wallet = load_wallet()
    print("\n👉 SUPPORTÉ : USD, BTC, ETH, SOL, USDT")
    token = input("Token à utiliser pour le paiement (ex: SOL) : ").strip().upper()
    if token not in wallet:
        print(f"\033[91mErreur : Le token '{token}' n'existe pas dans le wallet.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    try:
        amount_in = input("Montant de token à autoriser : ").strip()
        amount = float(amount_in)
    except ValueError:
        print("\033[91mErreur : Montant invalide.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    lat_in = input("Latitude (Optionnel, ex: 48.8566) : ").strip()
    lon_in = input("Longitude (Optionnel, ex: 2.3522) : ").strip()
    agency = input("Nom de l'agence de données mobile (Optionnel) : ").strip()
    dest_addr = input("Adresse de destination (Optionnel, défaut: 0x42d7c506A7B753efea2DAc0694289ED3Bb46599E) : ").strip()
    
    lat = float(lat_in) if lat_in else None
    lon = float(lon_in) if lon_in else None
    agency = agency if agency else "Agence de Validation Mobile"
    dest_addr = dest_addr if dest_addr else "0x42d7c506A7B753efea2DAc0694289ED3Bb46599E"
    
    print("\n\033[96m[Système] Demande d'autorisation de paiement mobilité...\033[0m")
    
    from mobility_payment import request_mobility_payment
    success, result = request_mobility_payment(token, amount, lat, lon, agency, dest_addr)
    
    if not success:
        print(f"\033[91mÉchec : {result}\033[0m")
    else:
        print("\n\033[92m┌" + "─" * 58 + "┐")
        print("│            AUTORISATION DE PAIEMENT MOBILITÉ             │")
        print("├" + "─" * 58 + "┤")
        print(f"│ Référence      : {result['reference']:<39} │")
        print(f"│ Statut         : {result['validation_status']:<39} │")
        print(f"│ Agence         : {result['agency']:<39} │")
        print(f"│ Approbation    : {result['approval_hash'][:35]:<39} │")
        print(f"│ Destination    : {result['destination_address'][:35]:<39} │")
        print(f"│ Débité         : {result['token_amount']:.6f} {result['token_used']:<30} │")
        print(f"│ Réserve USD    : +${result['usd_equivalent']:.2f} USD (Compte crédité)   │")
        print("└" + "─" * 58 + "┘\033[0m")
        
        # Display the map
        draw_mobility_map(result['geographic_alignment']['latitude'], result['geographic_alignment']['longitude'])
        print("\033[92m[Audio] Lecture audio de la confirmation en cours...\033[0m")
        
    input("\nAppuyez sur Entrée pour revenir au Lobby...")

def main():
    price_histories = {
        "BTC": [],
        "ETH": [],
        "SOL": [],
        "USDT": []
    }
    
    while True:
        clear_console()
        print_header()
        
        # Load fresh wallet and live prices
        wallet = load_wallet()
        prices, is_live = get_crypto_prices()
        
        # Initialize and update price history
        init_history_if_empty(price_histories, prices)
        for token, price in prices.items():
            if token in price_histories:
                price_histories[token].append(price)
                if len(price_histories[token]) > 10:
                    price_histories[token].pop(0)
        
        print_prices(prices, is_live)
        print_balances(wallet, prices)
        
        print(" [1] Effectuer un échange de tokens (Swap)")
        print(" [2] Parcourir l'historique des reçus audio")
        print(" [3] Réécouter la dernière transaction")
        print(" [4] Visualiser le rendu scopique (Graphique des prix)")
        print(" [5] Autorisation de paiement mobilité (Avec carte & tokens)")
        print(" [6] Quitter")
        print("-" * 60)
        
        choice = input("Choisissez une option (1-6) : ").strip()
        
        if choice == "1":
            menu_swap()
        elif choice == "2":
            menu_history()
        elif choice == "3":
            latest_mp3 = os.path.join(AUDIO_DIR, "latest_receipt.mp3")
            if os.path.exists(latest_mp3):
                print("\nLecture du dernier reçu...")
                play_audio_file(latest_mp3)
            else:
                print("\nAucun enregistrement trouvé.")
                import time
                time.sleep(1.5)
        elif choice == "4":
            menu_scopic(price_histories)
        elif choice == "5":
            menu_mobility()
        elif choice == "6":
            print("\nMerci d'avoir utilisé Crypto Lobby Wallet. Au revoir !")
            break
        else:
            print("\n\033[91mOption invalide !\033[0m")
            import time
            time.sleep(1)

if __name__ == "__main__":
    main()

