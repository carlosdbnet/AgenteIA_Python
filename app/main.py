import sys
import os
import threading
import json
import uvicorn
from fastapi import FastAPI, Request

# Fix: Add the project root to sys.path *BEFORE* absolute imports from app
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.whatsapp_service import start_whatsapp, send_whatsapp_message
from app.utils.script_runner import run_script

app = FastAPI(title="Shopfono AI Bot Webhook")

@app.get("/")
def home():
    return {"status": "online", "service": "Shopfono AI Bot"}



def run_bot():
    try:
        start_whatsapp()
    except Exception as e:
        print(f"Fatal Error in WhatsApp Client: {e}")

if __name__ == "__main__":
    # Inicia o WhatsApp em uma thread separada para não travar o FastAPI
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Inicia o Servidor Web (o Railway vai passar a porta via variável de ambiente PORT)
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

