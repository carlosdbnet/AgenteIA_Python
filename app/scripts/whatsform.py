import webbrowser
import sys

def main():
    url = "https://docs.google.com/forms/d/e/1FAIpQLSe56C7vxtRt_8F5veuV3yQqkJcpLgTFAuXaND0Co1RmNHtv6A/viewform?usp=publish-editor"
    
    # Se estiver rodando localmente com interface gráfica, tenta abrir o navegador
    # No servidor (Railway), isso não terá efeito visual, mas não quebra o script
    try:
        if sys.platform != "linux": # No Windows/Mac local costuma funcionar
            webbrowser.open(url)
    except:
        pass
        
    # O bot captura o que for impresso aqui e envia no WhatsApp
    print("📋 Formulário de Cadastro e Pedido:")
    print(url)
    print("\nPor favor, preencha os dados no link acima para prosseguirmos com seu atendimento! ✨")

if __name__ == "__main__":
    main()
