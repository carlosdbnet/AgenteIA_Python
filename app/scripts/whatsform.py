import webbrowser
import sys

def main():
    url = "https://whatsform.com/5orkql"
    
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
