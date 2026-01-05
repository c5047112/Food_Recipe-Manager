import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "recipe.db"

# -----------------------------
# Connect to SQLite DB
# -----------------------------
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# -----------------------------
# Create Tables
# -----------------------------

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_approved INTEGER DEFAULT 0,
    is_admin INTEGER DEFAULT 0
);
""")

# Recipes table
c.execute("""
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    ingredients TEXT NOT NULL,
    instructions TEXT NOT NULL,
    category TEXT,
    image_url TEXT,
    video_url TEXT,
    user_id INTEGER,
    delete_request INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY(user_id) REFERENCES users(id)
);
""")

# Reviews table
c.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(recipe_id) REFERENCES recipes(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);
""")

# -----------------------------
# Insert Default Admin
# -----------------------------
c.execute("SELECT * FROM users WHERE is_admin = 1")
admin = c.fetchone()

if not admin:
    c.execute("""
        INSERT INTO users (username, email, password, is_approved, is_admin)
        VALUES (?, ?, ?, 1, 1)
    """, ("admin", "admin@example.com", generate_password_hash("admin123")))

conn.commit()

# -----------------------------
# Verify Tables
# -----------------------------
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print("Tables in DB:", tables)

conn.close()
print("Database initialized successfully!")
