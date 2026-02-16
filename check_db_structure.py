import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("No DATABASE_URL found")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tables = cursor.fetchall()
    print("Tables found:", tables)
    
    for table in tables:
        t_name = table[0]
        print(f"\n--- Columns in {t_name} ---")
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t_name}'")
        cols = cursor.fetchall()
        for col in cols:
            print(f"{col[0]}: {col[1]}")
            
    conn.close()

except Exception as e:
    print(e)
