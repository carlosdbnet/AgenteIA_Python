import sys
import os

# Add the project root to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.whatsapp_service import start_whatsapp

if __name__ == "__main__":
    try:
        start_whatsapp()
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Fatal Error: {e}")
