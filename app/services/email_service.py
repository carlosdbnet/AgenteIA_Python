import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# Note: load_dotenv() should be called at the app entry point (main.py)
# so we don't call it here to avoid potential overrides or issues in production.

def send_registration_email(to_email, data):
    """
    Sends a registration confirmation email with all form data to the user.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Debug info (masked)
    print(f"🔍 Verificando variáveis no ambiente: HOST={'OK' if smtp_host else 'MISSING'}, USER={'OK' if smtp_user else 'MISSING'}, PASS={'OK' if smtp_password else 'MISSING'}")

    if not all([smtp_host, smtp_user, smtp_password]):
        missing = []
        if not smtp_host: missing.append("SMTP_HOST")
        if not smtp_user: missing.append("SMTP_USER")
        if not smtp_password: missing.append("SMTP_PASSWORD")
        print(f"⚠️ Erro: Variáveis detectadas como vazias no Railway: {', '.join(missing)}")
        print("💡 DICA: No Railway, verifique se você clicou em 'Apply Changes' após salvar as variáveis.")
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
        port_int = int(smtp_port)
        print(f"📧 Diagnóstico de rede para {smtp_host}:{port_int}...")
        
        # Test DNS resolution
        try:
            import socket
            ips = socket.gethostbyname_ex(smtp_host)
            print(f"🌐 IPs resolvidos para {smtp_host}: {ips[2]}")
        except Exception as dns_err:
            print(f"❌ Erro de DNS: {dns_err}")

        # Test HTTPS connectivity (Port 443) to confirm if its a general network issue or SMTP block
        try:
            print("🌐 Testando conectividade geral (google.com:443)...")
            test_s = socket.create_connection(("google.com", 443), timeout=5)
            test_s.close()
            print("✅ Internet OK (443 acessível). O bloqueio é específico para portas de E-mail (SMTP).")
        except Exception:
            print("❌ Internet parece inacessível ou conectividade geral bloqueada.")

        # Test socket connection directly (IPv4)
        try:
            print(f"🔌 Testando conexão socket para {smtp_host}:{port_int}...")
            s = socket.create_connection((smtp_host, port_int), timeout=10)
            s.close()
            print("🔗 Conexão socket estabelecida com sucesso!")
        except Exception as sock_err:
            print(f"❌ Socket recusado: {sock_err}")
            print(f"⚠️ O Railway parece estar bloqueando a porta {port_int}. Isso é comum em planos Starter/Trial.")
            if port_int == 465:
                print("💡 DICA: Tente a porta 587 (TLS).")
            elif port_int == 587:
                 print("💡 DICA: Tente a porta 2525 (se o seu provedor suportar).")

        # Real SMTP Connection
        if port_int == 465:
            server_class = smtplib.SMTP_SSL
        else:
            server_class = smtplib.SMTP

        with server_class(smtp_host, port_int, timeout=30) as server:
            if port_int != 465:
                print("🔐 Iniciando TLS...")
                server.starttls()
            
            print(f"🔑 Efetuando login ({smtp_user})...")
            server.login(smtp_user, smtp_password)
            print("📤 Enviando mensagem...")
            server.send_message(message)
            
        print(f"✅ Email enviado com sucesso para {to_email}")
        return True
    except Exception as e:
        print(f"❌ Erro fatal no envio: {e}")
        import traceback
        traceback.print_exc()
        return False
