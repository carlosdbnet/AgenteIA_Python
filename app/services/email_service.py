import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json

def send_via_brevo_api(to_email, data, html_content, api_key, sender_email):
    """
    Sends email via Brevo REST API (HTTPS Port 443) to bypass SMTP port blocks.
    """
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {"name": "Dbnet", "email": sender_email},
        "to": [{"email": to_email}],
        "subject": "Confirmação de Cadastro - Shopfono",
        "htmlContent": html_content
    }
    
    try:
        api_key_clean = api_key.strip() if api_key else ""
        print(f"🚀 Enviando via API Brevo (Porta 443)...")
        print(f" debug: Key len={len(api_key_clean)}, Prefix={api_key_clean[:5]}... (v3 expected)")
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        if response.status_code in [201, 202, 200]:
            print(f"✅ Email enviado com sucesso via API! (ID: {response.json().get('messageId')})")
            return True
        else:
            print(f"❌ Erro na API Brevo ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erno na requisição API: {e}")
        return False

def send_registration_email(to_email, data):
    """
    Sends a registration confirmation email with all form data to the user.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "2525")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Debug info (masked)
    print(f"🔍 Verificando variáveis no ambiente: HOST={'OK' if smtp_host else 'MISSING'}, USER={'OK' if smtp_user else 'MISSING'}, PASS={'OK' if smtp_password else 'MISSING'}")

    if not all([smtp_host, smtp_user, smtp_password]):
        print(f"⚠️ Erro: Credenciais incompletas. Verifique SMTP_USER e SMTP_PASSWORD.")
        return False

    # HTML Body
    html_content = f"""
    <html>
    <body style="font-family: sans-serif; color: #1e293b; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
            <h2 style="color: #6366f1; text-align: center;">Olá {data.get('Nome')}, seu cadastro foi recebido!</h2>
            <p>Obrigado por se cadastrar na Shopfono. Confira abaixo os dados enviados:</p>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <tr style="background-color: #f1f5f9;">
                    <th style="padding: 10px; border: 1px solid #e2e8f0; text-align: left;">Campo</th>
                    <th style="padding: 10px; border: 1px solid #e2e8f0; text-align: left;">Valor</th>
                </tr>
    """
    
    for key, value in data.items():
        html_content += f"""
                <tr>
                    <td style="padding: 10px; border: 1px solid #e2e8f0; font-weight: bold;">{key}</td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;">{value}</td>
                </tr>
        """
        
    html_content += """
            </table>
            
            <p style="margin-top: 30px; text-align: center; color: #64748b; font-size: 0.9rem;">
                Este é um email automático. Por favor, não responda.
            </p>
        </div>
    </body>
    </html>
    """

    # If it's Brevo, use API by default as SMTP is blocked on Railway
    if smtp_host and "brevo" in smtp_host.lower():
        return send_via_brevo_api(to_email, data, html_content, smtp_password, smtp_user)

    # Fallback/Legacy SMTP for other providers
    # [Rest of existing SMTP logic if needed, but for now we focus on Brevo fix]
    try:
        # Create Message
        message = MIMEMultipart()
        message["From"] = smtp_user
        message["To"] = to_email
        message["Subject"] = "Confirmação de Cadastro - Shopfono"
        message.attach(MIMEText(html_content, "html"))

        port_int = int(smtp_port)
        if port_int == 465:
            server_class = smtplib.SMTP_SSL
        else:
            server_class = smtplib.SMTP

        with server_class(smtp_host, port_int, timeout=30) as server:
            if port_int != 465:
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        return True
    except Exception as e:
        print(f"❌ Erro SMTP: {e}. Considere usar um serviço que suporte HTTP API.")
        return False
