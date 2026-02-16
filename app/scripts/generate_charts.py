import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not set in environment.")
    # Don't exit here if imported, just return
else:
    pass

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def generate_charts():
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database for chart generation.")
        return

    try:
        # Determine charts directory absolute path
        # Check if running as script or imported
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # go up one level to 'app' then 'charts'
        # script is in app/scripts/, so up one level is app/
        app_dir = os.path.dirname(current_dir) 
        charts_dir = os.path.join(app_dir, "charts")
        
        if not os.path.exists(charts_dir):
            os.makedirs(charts_dir)

        # --- 1. Pie Chart: User Distribution ---
        
        print("📊 Generating User Pie Chart...")
        query_users = "SELECT name, phone FROM users"
        df_users = pd.read_sql_query(query_users, conn)

        if not df_users.empty:
            user_counts = df_users['name'].value_counts()
            
            plt.figure(figsize=(10, 8))
            plt.pie(user_counts, labels=user_counts.index, autopct='%1.1f%%', startangle=140)
            plt.title('Participação de Chamadas por Usuário (Simulado: Distribuição de Usuários)')
            plt.axis('equal')
            
            output_path_pie = os.path.join(charts_dir, "grafico_pizza_usuarios.png")
            plt.savefig(output_path_pie)
            print(f"✅ User Pie Chart saved to {output_path_pie}")
            plt.close()
        else:
            print("⚠️ No data found in 'users' table.")

        # --- 2. Bar Chart: Registration Names ---
        print("📊 Generating Registration Bar Chart...")
        query_registrations = "SELECT nome FROM registrations"
        df_registrations = pd.read_sql_query(query_registrations, conn)

        if not df_registrations.empty:
            name_counts = df_registrations['nome'].value_counts().head(10) # Top 10 names
            
            plt.figure(figsize=(12, 6))
            name_counts.plot(kind='bar', color='skyblue')
            plt.title('Participação por Nome (Top 10 Cadastros)')
            plt.xlabel('Nome')
            plt.ylabel('Quantidade')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            output_path_bar = os.path.join(charts_dir, "grafico_barra_cadastros.png")
            plt.savefig(output_path_bar)
            print(f"✅ Registration Bar Chart saved to {output_path_bar}")
            plt.close()
        else:
            print("⚠️ No data found in 'registrations' table.")

    except Exception as e:
        print(f"❌ Error generating charts: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    generate_charts()
