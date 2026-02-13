import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Database path - use /data for Railway persistent volume, fallback to local
DB_DIR = os.getenv("DB_PATH", "./data")
Path(DB_DIR).mkdir(parents=True, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "users.db")

def init_database():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")

def get_user_by_phone(phone: str):
    """Get user by phone number. Returns dict or None."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def create_user(phone: str, name: str):
    """Create a new user. Returns True if successful, False if user already exists."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO users (phone, name) VALUES (?, ?)",
            (phone, name)
        )
        
        conn.commit()
        conn.close()
        print(f"✅ User created: {name} ({phone})")
        return True
    except sqlite3.IntegrityError:
        print(f"⚠️ User already exists: {phone}")
        return False

def update_last_interaction(phone: str):
    """Update the last_interaction timestamp for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET last_interaction = CURRENT_TIMESTAMP WHERE phone = ?",
        (phone,)
    )
    
    conn.commit()
    conn.close()

def get_all_users():
    """Get all users (for debugging/admin purposes)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users ORDER BY last_interaction DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# Initialize database on module import
init_database()
