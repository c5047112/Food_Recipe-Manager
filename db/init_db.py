import sqlite3
from werkzeug.security import generate_password_hash

# Connect to DB
conn = sqlite3.connect("recipe.db")
c = conn.cursor()

# Load schema.sql
with open("schema.sql", "r") as f:
    c.executescript(f.read())

# Insert default admin if not exists
c.execute("SELECT * FROM users WHERE is_admin = 1")
admin = c.fetchone()

if not admin:
    c.execute("""
        INSERT INTO users (username, email, password, is_approved, is_admin)
        VALUES (?, ?, ?, 1, 1)
    """, ("admin", "admin@example.com", generate_password_hash("admin123")))

conn.commit()
conn.close()

print("Database initialized successfully!")
