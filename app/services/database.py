import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from dotenv import load_dotenv

# Force load .env to ensure DATABASE_URL is available even if imported early
load_dotenv()

# PostgreSQL connection using DATABASE_URL from Railway
# We will fetch it dynamically in get_connection to be safe, but keep a module level default for init
_DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Create and return a PostgreSQL connection."""
    # Re-fetch or use cached
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ [DB] DATABASE_URL environment variable not set!")
        raise ValueError("DATABASE_URL environment variable not set")
        
    print(f"🔵 [DB] Connecting to PostgreSQL...")
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

def init_db():
    """Initialize the database and create tables if they don't exist."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                phone VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create registrations table for form submissions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                telefone VARCHAR(20) NOT NULL,
                whatsapp VARCHAR(20),
                cep VARCHAR(10),
                endereco VARCHAR(255),
                numero VARCHAR(20),
                complemento VARCHAR(255),
                bairro VARCHAR(100),
                cidade VARCHAR(100),
                estado VARCHAR(2),
                genero VARCHAR(50),
                cpf_cnpj VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ PostgreSQL database initialized successfully (users + registrations tables)")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

def get_user_by_phone(phone):
    """Get user by phone number."""
    print(f"🔍 [DB] Looking up user by phone: {phone}")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            print(f"✅ [DB] User found: {user['name']} (ID: {user['id']})")
        else:
            print(f"❌ [DB] User NOT found for phone: {phone}")
        
        return user
    except Exception as e:
        print(f"❌ [DB] CRITICAL ERROR getting user: {e}")
        print(f"❌ [DB] Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def create_user(phone, name):
    """Create a new user."""
    print(f"🔵 [DB] Attempting to create user: {name} ({phone})")
    try:
        conn = get_connection()
        print(f"🔵 [DB] Connection established successfully")
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO users (phone, name) VALUES (%s, %s) RETURNING id",
            (phone, name)
        )
        user_id = cursor.fetchone()['id']
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ [DB] User created successfully: {name} ({phone}) - ID: {user_id}")
        return user_id
    except psycopg2.IntegrityError as e:
        print(f"⚠️ [DB] User already exists: {phone} - {e}")
        return None
    except Exception as e:
        print(f"❌ [DB] CRITICAL ERROR creating user: {e}")
        print(f"❌ [DB] Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def update_last_interaction(phone):
    """Update the last interaction timestamp for a user."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET last_interaction = %s WHERE phone = %s",
            (datetime.now(), phone)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error updating last interaction: {e}")

def get_all_users():
    """Get all users (for admin purposes)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return users
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []

# ===== REGISTRATION FORM FUNCTIONS =====

def create_registration(data):
    """Create a new registration from form data."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO registrations 
            (nome, email, telefone, whatsapp, cep, endereco, numero, complemento, 
             bairro, cidade, estado, genero, cpf_cnpj)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('nome'),
            data.get('email'),
            data.get('telefone'),
            data.get('whatsapp'),
            data.get('cep'),
            data.get('endereco'),
            data.get('numero'),
            data.get('complemento'),
            data.get('bairro'),
            data.get('cidade'),
            data.get('estado'),
            data.get('genero'),
            data.get('cpf_cnpj')
        ))
        
        registration_id = cursor.fetchone()['id']
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Registration saved to database: {data.get('nome')} (ID: {registration_id})")
        return registration_id
    except Exception as e:
        print(f"❌ Error saving registration: {e}")
        return None

def get_all_registrations():
    """Get all registrations (for admin purposes)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM registrations ORDER BY created_at DESC")
        registrations = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return registrations
    except Exception as e:
        print(f"Error getting all registrations: {e}")
        return []

# Initialize database on module import
try:
    init_db()
except Exception as e:
    print(f"⚠️ Could not initialize database on import: {e}")
    print("Database will be initialized on first connection attempt")
