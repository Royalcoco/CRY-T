import os
import sys

# Configure UTF-8 on Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

from cli import draw_scopic_chart

def test_chart():
    print("=== DÉBUT DU TEST DU RENDU SCOPIQUE ===")
    
    # 10 test points showing oscillations
    history = [65000.0, 65042.0, 65020.0, 65085.0, 65110.0, 65095.0, 65140.0, 65120.0, 65180.0, 65165.0]
    
    try:
        draw_scopic_chart("BTC", history)
        print("\n[PASS] Le rendu scopique s'est affiché sans erreur.")
        return True
    except Exception as e:
        print(f"\n[FAIL] Erreur de rendu scopique : {e}")
        return False

if __name__ == "__main__":
    test_chart()
