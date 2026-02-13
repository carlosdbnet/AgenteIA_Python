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

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from app.services.whatsapp_service import start_whatsapp, send_whatsapp_message
from app.utils.script_runner import run_script

app = FastAPI(title="Shopfono AI Bot Webhook")

@app.get("/")
def home():
    return {"status": "online", "service": "Shopfono AI Bot", "version": "1.4.0 - PostgreSQL"}

@app.get("/cadastro", response_class=HTMLResponse)
async def get_form():
    template_path = os.path.join(project_root, "app", "templates", "form.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Erro: Template não encontrado</h1>"

@app.post("/cadastro")
async def post_form(
    pessoa: str = Form(...),
    nome: str = Form(...),
    sobrenome: str = Form(...),
    email: str = Form(...),
    data_nascimento: str = Form(...),
    genero: str = Form(...),
    cpf_cnpj: str = Form(...),
    telefone: str = Form(...),
    cep: str = Form(...),
    rua_av: str = Form(...),
    numero: str = Form(...),
    bairro: str = Form(...),
    cidade: str = Form(...),
    uf: str = Form(...)
):
    data = {
        "Pessoa": pessoa,
        "Nome": nome,
        "Sobrenome": sobrenome,
        "Email": email,
        "Data Nascimento": data_nascimento,
        "Genero": genero,
        "Cpf/Cnpj": cpf_cnpj,
        "Telefone": telefone,
        "CEP": cep,
        "Rua/Av": rua_av,
        "Numero": numero,
        "Bairro": bairro,
        "Cidade": cidade,
        "UF": uf
    }
    
    # Salva no Excel via script
    data_str = json.dumps(data)
    run_script("save_to_excel", [data_str])
    
    # Notifica o cliente via WhatsApp se possível
    msg = f"Olá {nome}! Recebemos seu cadastro com sucesso. 📝✅\n\nNossa equipe em breve entrará em contato. Obrigado!"
    print(f"📞 Iniciando notificação WhatsApp para {telefone}...")
    send_whatsapp_message(telefone, msg)
    
    # Envia o e-mail de confirmação
    print(f"✉️ Iniciando envio de e-mail para {email}...")
    from app.services.email_service import send_registration_email
    send_registration_email(email, data)
    print("✨ Processo de cadastro finalizado.")
    
    return HTMLResponse(content=f"""
        <div style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #6366f1;">Obrigado, {nome}!</h1>
            <p>Seus dados foram enviados com sucesso e uma confirmação foi enviada para {email}.</p>
            <a href="/cadastro" style="color: #6366f1; text-decoration: none; font-weight: bold;">Voltar</a>
        </div>
    """, status_code=200)



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

