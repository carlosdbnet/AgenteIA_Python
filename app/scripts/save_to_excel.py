import pandas as pd
import os
import sys
import json
from datetime import datetime

EXCEL_FILE = "vendas.xlsx"

def main():
    if len(sys.argv) < 2:
        print("Erro: Nenhum dado recebido.")
        return

    try:
        # Recebe os dados como uma string JSON (mais seguro para dados complexos)
        raw_data = sys.argv[1]
        data = json.loads(raw_data)
        
        # Adiciona timestamp
        data['Data_Processamento'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        df_new = pd.DataFrame([data])
        
        if os.path.exists(EXCEL_FILE):
            df_existing = pd.read_excel(EXCEL_FILE)
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
            df_final.to_excel(EXCEL_FILE, index=False)
        else:
            df_new.to_excel(EXCEL_FILE, index=False)
            
        print(f"✅ Dados gravados com sucesso em {EXCEL_FILE}")
        
    except Exception as e:
        print(f"❌ Erro ao processar Excel: {str(e)}")

if __name__ == "__main__":
    main()
