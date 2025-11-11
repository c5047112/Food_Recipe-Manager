# Import required Flask modules
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3  # To interact with the SQLite database
from werkzeug.security import generate_password_hash, check_password_hash

# Create Flask app instance
app = Flask(__name__)

# Secret key for sessions and flash messages
app.secret_key = "supersecretkey"

# Database file path
DB_PATH = 'recipe.db'


# ------------------------------------------------------------
# 🧱 DATABASE INITIALIZATION FUNCTION
# ------------------------------------------------------------
def init_db():
    """Create database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # USERS TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')

    # RECIPES TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL,
            category TEXT,
            image_url TEXT,
            created_by INTEGER,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
    ''')

    conn.commit()

    # CHECK IF ADMIN EXISTS
    c.execute("SELECT * FROM users WHERE role='admin'")
    admin_exists = c.fetchone()

    # ADD DEFAULT ADMIN IF NOT EXISTS
    if not admin_exists:
        admin_pass = generate_password_hash('admin@1004')
        c.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ('admin', 'admin1004@gmail.com', admin_pass, 'admin')
        )
        conn.commit()
        print("✅ Default admin created successfully!")
        print("   Email: admin1004@gmail.com")
        print("   Password: admin@1004")

    conn.close()


# ------------------------------------------------------------
# 🧍‍♂️ USER REGISTRATION
# ------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already exists! Try logging in.", "warning")
            conn.close()
            return redirect(url_for('login'))

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            (username, email, hashed_password, 'user')
        )

        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ------------------------------------------------------------
# 🔐 USER LOGIN
# ------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]

            if user[4] == 'admin':
                flash("Welcome Admin!", "info")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Login successful!", "info")
                return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid email or password. Try again!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


# ------------------------------------------------------------
# 🧑‍🍳 USER DASHBOARD
# ------------------------------------------------------------
@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', username=session['username'])


# ------------------------------------------------------------
# 👑 ADMIN DASHBOARD
# ------------------------------------------------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', username=session['username'])


# ------------------------------------------------------------
# 🚪 LOGOUT ROUTES
# ------------------------------------------------------------
@app.route('/logoutuser')
def userLogout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))


@app.route('/logoutadmin')
def adminLogout():
    session.clear()
    flash("Admin has been logged out successfully.", "info")
    return redirect(url_for('login'))


# ------------------------------------------------------------
# 🏠 HOME PAGE
# ------------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')


# ------------------------------------------------------------
# 🚀 MAIN APP ENTRY POINT
# ------------------------------------------------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
