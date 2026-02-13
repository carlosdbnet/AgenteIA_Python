import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

# PostgreSQL connection using DATABASE_URL from Railway
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Create and return a PostgreSQL connection."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

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
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ PostgreSQL database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

def get_user_by_phone(phone):
    """Get user by phone number."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def create_user(phone, name):
    """Create a new user."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO users (phone, name) VALUES (%s, %s) RETURNING id",
            (phone, name)
        )
        user_id = cursor.fetchone()['id']
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ User created: {name} ({phone})")
        return user_id
    except psycopg2.IntegrityError:
        print(f"⚠️ User already exists: {phone}")
        return None
    except Exception as e:
        print(f"❌ Error creating user: {e}")
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

# Initialize database on module import
try:
    init_db()
except Exception as e:
    print(f"⚠️ Could not initialize database on import: {e}")
    print("Database will be initialized on first connection attempt")
