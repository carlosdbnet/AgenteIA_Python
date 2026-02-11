import pandas as pd
import os
from datetime import datetime

EXCEL_FILE = "vendas.xlsx"

def save_to_excel(data):
    """
    Saves the received webhook data into an Excel spreadsheet.
    :param data: Dictionary containing form fields.
    """
    # Adiciona a data e hora do recebimento
    data['Data_Hora_Recebimento'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Converte o dicionário em um DataFrame do Pandas
    df_new = pd.DataFrame([data])
    
    if os.path.exists(EXCEL_FILE):
        # Se o arquivo já existe, lê e concatena
        try:
            df_existing = pd.read_excel(EXCEL_FILE)
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
            df_final.to_excel(EXCEL_FILE, index=False)
            print(f"✅ Dados adicionados com sucesso ao arquivo {EXCEL_FILE}")
        except Exception as e:
            print(f"⚠️ Erro ao atualizar Excel: {e}")
            # Tenta salvar como novo se falhar a leitura
            df_new.to_excel(EXCEL_FILE, index=False)
    else:
        # Se não existe, cria um novo
        df_new.to_excel(EXCEL_FILE, index=False)
        print(f"📊 Novo arquivo {EXCEL_FILE} criado com os dados.")

    return EXCEL_FILE
