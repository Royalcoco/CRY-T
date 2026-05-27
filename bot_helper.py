import sys
import json
import os

# Set UTF-8 encoding on Windows to prevent output crashes
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from exchange import get_crypto_prices, swap_tokens
from cli import send_receipt_network
from audio_renderer import generate_receipt_audio

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command argument"}))
        return
        
    command = sys.argv[1].lower()
    
    if command == "prices":
        prices, is_live = get_crypto_prices()
        print(json.dumps({"prices": prices, "is_live": is_live}))
        
    elif command == "swap":
        if len(sys.argv) < 5:
            print(json.dumps({"error": "Usage: swap <from_token> <to_token> <amount>"}))
            return
        from_token = sys.argv[2]
        to_token = sys.argv[3]
        try:
            amount = float(sys.argv[4])
        except ValueError:
            print(json.dumps({"error": "Invalid amount"}))
            return
            
        success, receipt, err = swap_tokens(from_token, to_token, amount)
        if not success:
            print(json.dumps({"success": False, "error": err}))
            return
            
        # Send over network (form-like request)
        network_sent = send_receipt_network(receipt)
        receipt["network_sent"] = network_sent
        
        # Generate audio message (saved to audio_logs)
        audio_path = generate_receipt_audio(receipt)
        receipt["audio_path"] = audio_path
        
        print(json.dumps({"success": True, "receipt": receipt}))
        
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))

if __name__ == "__main__":
    main()
