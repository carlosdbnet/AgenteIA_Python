import sys

def main():
    if len(sys.argv) < 2:
        print("Uso: hello.py [nome] [outros_argumentos...]")
        return
    
    nome = sys.argv[1]
    args = sys.argv[2:]
    
    print(f"Olá, {nome}! 👋")
    if args:
        print(f"Recebi os seguintes argumentos extras: {', '.join(args)}")
    print("Script executado com sucesso no servidor! ✅")

if __name__ == "__main__":
    main()
