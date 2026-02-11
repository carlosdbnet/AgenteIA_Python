import sys
import os
import threading
import json
import uvicorn
from fastapi import FastAPI, Request
from app.services.whatsapp_service import start_whatsapp
from app.utils.script_runner import run_script

# Add the project root to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Shopfono AI Bot Webhook")

@app.get("/")
def home():
    return {"status": "online", "service": "Shopfono AI Bot"}

@app.post("/webhook/whatsform")
async def whatsform_webhook(request: Request):
    try:
        data = await request.json()
        print(f"📥 Webhook recebido do WhatsForm: {data}")
        
        # Converte os dados em JSON string para passar ao script
        data_str = json.dumps(data)
        
        # Executa o script de salvamento (passando os dados como parâmetro)
        output = run_script("save_to_excel", [data_str])
        
        print(f"🖥️ Saída do script: {output}")
        return {"status": "success", "message": "Dados processados pelo script", "output": output}
    except Exception as e:
        print(f"❌ Erro no Webhook: {e}")
        return {"status": "error", "message": str(e)}

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

