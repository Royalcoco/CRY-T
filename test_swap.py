import os
import json
import time
from exchange import load_wallet, swap_tokens
from cli import display_receipt_form, send_receipt_network
from audio_renderer import generate_receipt_audio, play_audio_file, AUDIO_DIR

def run_tests():
    print("=== DEBUT DE LA VERIFICATION DU CYCLE DE SWAP ===")
    
    # 1. Verification de l'état initial
    wallet = load_wallet()
    print(f"[Verification] Solde initial USD : {wallet['USD']} | BTC : {wallet['BTC']}")
    
    initial_usd = wallet['USD']
    if initial_usd < 1000:
        print("[System] Remise à niveau du solde USD pour les tests...")
        wallet['USD'] = 10000.0
        from exchange import save_wallet
        save_wallet(wallet)
        initial_usd = 10000.0
        
    # 2. Execution du Swap (1000 USD -> BTC)
    print("\n[Verification] Execution du Swap : Échange de 1000 USD contre du BTC...")
    success, receipt, err = swap_tokens("USD", "BTC", 1000.0)
    
    if not success:
        print(f"[FAIL] Échec du swap : {err}")
        return False
        
    print("[PASS] Le swap s'est déroulé avec succès.")
    
    # 3. Affichage du Reçu
    display_receipt_form(receipt)
    
    # 4. Verification de la mise à jour du Wallet
    updated_wallet = load_wallet()
    print(f"\n[Verification] Solde mis à jour USD : {updated_wallet['USD']} | BTC : {updated_wallet['BTC']}")
    
    if updated_wallet['USD'] != initial_usd - 1000.0:
        print("[FAIL] Le solde USD n'a pas été débité correctement.")
        return False
    if updated_wallet['BTC'] <= 0.0:
        print("[FAIL] Le solde BTC n'a pas été crédité.")
        return False
        
    print("[PASS] La persistance et la logique du portefeuille fonctionnent.")
    
    # 5. Test de transmission réseau
    network_success = send_receipt_network(receipt)
    if network_success:
        print("[PASS] La transmission réseau du formulaire de reçu a fonctionné.")
    else:
        print("[WARNING] La transmission réseau a échoué (vérifiez votre connexion).")

    # 6. Test audio
    print("\n[Verification] Génération de l'audio MP3...")
    audio_path = generate_receipt_audio(receipt)
    if audio_path and os.path.exists(audio_path):
        print(f"[PASS] Fichier audio généré à : {audio_path}")
        print("[Verification] Lecture audio du reçu en cours...")
        play_audio_file(audio_path)
        # Wait a few seconds to let the background thread start playing the audio before finishing the test script
        time.sleep(4)
    else:
        print("[FAIL] Échec de la génération audio.")
        return False
        
    print("\n=== VERIFICATION TERMINEE AVEC SUCCÈS ===")
    return True

if __name__ == "__main__":
    run_tests()
