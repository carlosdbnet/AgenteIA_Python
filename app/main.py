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
    return {"status": "online", "service": "Shopfono AI Bot", "version": "1.5.2 - Debug Logging"}

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
    # Prepara os dados do formulário para o banco de dados
    # Note: 'whatsapp', 'endereco', 'complemento' are not directly from form,
    # using 'telefone' for whatsapp and combining 'rua_av' for 'endereco'.
    data = {
        "nome": nome,
        "email": email,
        "telefone": telefone,
        "whatsapp": telefone, # Assuming whatsapp is the same as telefone for now
        "cep": cep,
        "endereco": f"{rua_av}, {numero}", # Combining rua_av and numero for endereco
        "complemento": "", # No direct form field for complemento
        "numero": numero,
        "bairro": bairro,
        "cidade": cidade,
        "estado": uf,
        "genero": genero,
        "cpf_cnpj": cpf_cnpj
    }
    
    # Salva no PostgreSQL
    print(f"💾 Salvando cadastro no banco de dados...")
    from app.services import database
    registration_id = database.create_registration(data)
    
    if not registration_id:
        print("⚠️ Falha ao salvar no banco de dados, mas continuando com email...")
    
    # Prepara os dados para o Excel (mantido para compatibilidade)
    data_excel = {
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
    data_str = json.dumps(data_excel)
    run_script("save_to_excel", [data_str])
    
    # Notifica o cliente via WhatsApp se possível
    msg = f"Olá {nome}! Recebemos seu cadastro com sucesso. 📝✅\n\nNossa equipe em breve entrará em contato. Obrigado!"
    print(f"📞 Iniciando notificação WhatsApp para {telefone}...")
    send_whatsapp_message(telefone, msg)
    
    # Envia o e-mail de confirmação
    print(f"✉️ Iniciando envio de e-mail para {email}...")
    from app.services.email_service import send_registration_email
    send_registration_email(email, data_excel)
    print("✨ Processo de cadastro finalizado.")
    
    return HTMLResponse(content=f"""
        <div style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #6366f1;">Obrigado, {nome}!</h1>
            <p>Seus dados foram enviados com sucesso e uma confirmação foi enviada para {email}.</p>
            <a href="/cadastro" style="color: #6366f1; text-decoration: none; font-weight: bold;">Voltar</a>
        </div>
    """, status_code=200)

@app.get("/admin/registrations", response_class=HTMLResponse)
async def view_registrations():
    """Admin endpoint to view all registrations from PostgreSQL."""
    from app.services import database
    
    registrations = database.get_all_registrations()
    
    # Build HTML table
    rows_html = ""
    for reg in registrations:
        rows_html += f"""
        <tr>
            <td>{reg['id']}</td>
            <td>{reg['nome']}</td>
            <td>{reg['email']}</td>
            <td>{reg['telefone']}</td>
            <td>{reg['whatsapp'] or '-'}</td>
            <td>{reg['cep'] or '-'}</td>
            <td>{reg['endereco'] or '-'}</td>
            <td>{reg['numero'] or '-'}</td>
            <td>{reg['complemento'] or '-'}</td>
            <td>{reg['bairro'] or '-'}</td>
            <td>{reg['cidade'] or '-'}</td>
            <td>{reg['estado'] or '-'}</td>
            <td>{reg['genero'] or '-'}</td>
            <td>{reg['cpf_cnpj'] or '-'}</td>
            <td>{reg['created_at'].strftime('%d/%m/%Y %H:%M') if reg['created_at'] else '-'}</td>
        </tr>
        """
    
    total = len(registrations)
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin - Cadastros</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 2rem;
                margin-bottom: 10px;
            }}
            .stats {{
                background: rgba(255,255,255,0.1);
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
                display: inline-block;
            }}
            .stats span {{
                font-size: 1.5rem;
                font-weight: bold;
            }}
            .table-container {{
                overflow-x: auto;
                padding: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 0.9rem;
            }}
            th {{
                background: #6366f1;
                color: white;
                padding: 12px 8px;
                text-align: left;
                font-weight: 600;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            td {{
                padding: 10px 8px;
                border-bottom: 1px solid #e5e7eb;
            }}
            tr:hover {{
                background: #f3f4f6;
            }}
            tr:nth-child(even) {{
                background: #f9fafb;
            }}
            tr:nth-child(even):hover {{
                background: #f3f4f6;
            }}
            .empty {{
                text-align: center;
                padding: 60px 20px;
                color: #6b7280;
            }}
            .empty h2 {{
                font-size: 1.5rem;
                margin-bottom: 10px;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #6b7280;
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Cadastros Registrados</h1>
                <div class="stats">
                    Total de cadastros: <span>{total}</span>
                </div>
            </div>
            
            {"<div class='table-container'><table><thead><tr><th>ID</th><th>Nome</th><th>Email</th><th>Telefone</th><th>WhatsApp</th><th>CEP</th><th>Endereço</th><th>Número</th><th>Complemento</th><th>Bairro</th><th>Cidade</th><th>Estado</th><th>Gênero</th><th>CPF/CNPJ</th><th>Data Cadastro</th></tr></thead><tbody>" + rows_html + "</tbody></table></div>" if total > 0 else "<div class='empty'><h2>Nenhum cadastro encontrado</h2><p>Os cadastros aparecerão aqui assim que forem enviados pelo formulário.</p></div>"}
            
            <div class="footer">
                Shopfono AI Bot v1.5.0 - Admin Panel
            </div>
        </div>
    </body>
    </html>
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

