import os
import subprocess
import threading
from gtts import gTTS

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio_logs")

def ensure_audio_dir():
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

def play_audio_file(file_path):
    """Play MP3 file asynchronously in a separate thread using PowerShell WMPlayer.OCX."""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return
        
    def _play():
        # PowerShell script to play audio using COM Object Windows Media Player
        # Escaping quotes for powershell command
        ps_cmd = (
            f"$player = New-Object -ComObject WMPlayer.OCX; "
            f"$player.URL = '{abs_path}'; "
            f"$player.controls.play(); "
            f"while ($player.playState -ne 1) {{ Start-Sleep -Milliseconds 100 }}"
        )
        cmd = ["powershell", "-Command", ps_cmd]
        # Run hidden without showing windows or capturing terminal output
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    thread = threading.Thread(target=_play, daemon=True)
    thread.start()

def generate_receipt_audio(receipt):
    """
    Generate speech MP3 file from exchange receipt.
    Returns the path to the generated MP3 file, or None if error.
    """
    ensure_audio_dir()
    
    from_amount = receipt["from_amount"]
    from_token = receipt["from_token"]
    to_amount = receipt["to_amount"]
    to_token = receipt["to_token"]
    
    # Text in French
    text = (
        f"Échange réussi. "
        f"Vous avez échangé {from_amount} {from_token} "
        f"pour un montant reçu de {to_amount:.6f} {to_token}."
    )
    
    filename = f"receipt_{receipt['id']}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    latest_filepath = os.path.join(AUDIO_DIR, "latest_receipt.mp3")
    
    try:
        # Generate using gTTS (French language)
        tts = gTTS(text=text, lang="fr", slow=False)
        tts.save(filepath)
        
        # Also save as latest_receipt.mp3 for easy replay
        tts.save(latest_filepath)
        
        return filepath
    except Exception as e:
        # If offline or error occurs, print a subtle message
        # and don't raise error to avoid crashing the transaction flow
        print(f"\n[Avis] Impossible de générer l'audio (hors-ligne ou erreur) : {e}")
        return None
