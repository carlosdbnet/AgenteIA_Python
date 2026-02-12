import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_registration_email(to_email, data):
    """
    Sends a registration confirmation email with all form data to the user.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", 587)
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_user, smtp_password]):
        print("⚠️ Erro: Credenciais SMTP não configuradas no .env. Email não enviado.")
        return False

    # Create Message
    message = MIMEMultipart()
    message["From"] = smtp_user
    message["To"] = to_email
    message["Subject"] = "Confirmação de Cadastro - Shopfono"

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

    message.attach(MIMEText(html_content, "html"))

    try:
        print(f"📧 Tentando enviar email via {smtp_host}:{smtp_port}...")
        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        print(f"✅ Email enviado com sucesso para {to_email}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar email para {to_email}: {e}")
        import traceback
        traceback.print_exc()
        return False
