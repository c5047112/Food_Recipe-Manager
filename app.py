# ------------------------------------------------------------
# 🍽️ FOOD & RECIPE MANAGER — Flask Application
# ------------------------------------------------------------
# Features:
# ✅ User Registration & Login (with hashed passwords)
# ✅ Role-based access (Admin/User)
# ✅ Add, View, Edit, Delete Recipes
# ✅ SQLite database
# ✅ Flash messages for user feedback
# ✅ Content-block based templates (Jinja2)
# ------------------------------------------------------------

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------------------------------------------
# ⚙️ Flask App Configuration
# ------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Used for session and flash message encryption

DB_PATH = 'recipe.db'  # SQLite database file path


# ------------------------------------------------------------
# 🧱 DATABASE INITIALIZATION
# ------------------------------------------------------------
def init_db():
    """Creates required tables if they don’t exist and adds a default admin."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # USERS TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )''')

    # RECIPES TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        ingredients TEXT NOT NULL,
        instructions TEXT NOT NULL,
        category TEXT,
        image_url TEXT,
        created_by INTEGER,
        FOREIGN KEY(created_by) REFERENCES users(id)
    )''')

    # Default Admin (if not already present)
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        admin_pass = generate_password_hash('admin@1004')
        c.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ('admin', 'admin1004@gmail.com', admin_pass, 'admin')
        )
        print("✅ Default admin created → Email: admin1004@gmail.com | Password: admin@1004")

    conn.commit()
    conn.close()


# ------------------------------------------------------------
# 🧍‍♂️ USER REGISTRATION
# ------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Allows new users to register and stores their info securely."""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Check if user already exists
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = c.fetchone()

        if existing_user:
            flash("Email already exists! Try logging in.", "warning")
            conn.close()
            return redirect(url_for('login'))

        # Hash password before saving
        hashed_password = generate_password_hash(password)
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, hashed_password))
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
    """Handles user login with password verification."""
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        # Validate user and password
        if not user:
            flash("Email not found! Please register first.", "warning")
            return redirect(url_for('register'))

        if check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]

            flash("Login successful! Welcome back!", "success")
            if user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            flash("Incorrect password! Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


# ------------------------------------------------------------
# 🏠 HOME PAGE
# ------------------------------------------------------------
@app.route('/')
def home():
    """Home page (public)."""
    return render_template('index.html')


# ------------------------------------------------------------
# 👤 USER DASHBOARD
# ------------------------------------------------------------
@app.route('/user_dashboard')
def user_dashboard():
    """Dashboard shown after successful login."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', username=session['username'])


# ------------------------------------------------------------
# 🍳 ADD RECIPE
# ------------------------------------------------------------
@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    """Allows users to add new recipes."""
    if 'user_id' not in session:
        flash("Please log in to add a recipe.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        category = request.form['category']
        image_url = request.form['image_url']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO recipes (title, ingredients, instructions, category, image_url, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, ingredients, instructions, category, image_url, session['user_id']))
        conn.commit()
        conn.close()

        flash("Recipe added successfully!", "success")
        return redirect(url_for('view_recipes'))

    return render_template('add_recipe.html', username=session['username'])


# ------------------------------------------------------------
# 📖 VIEW RECIPES
# ------------------------------------------------------------
@app.route('/view_recipes')
def view_recipes():
    """Displays recipes created by the logged-in user."""
    if 'user_id' not in session:
        flash("Please log in to view your recipes.", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM recipes WHERE created_by=?", (session['user_id'],))
    recipes = c.fetchall()
    conn.close()

    return render_template('view_recipes.html', recipes=recipes, username=session['username'])


# ------------------------------------------------------------
# ✏️ EDIT RECIPE
# ------------------------------------------------------------
@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """Allows the user to edit their recipe."""
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Handle form submission
    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        category = request.form['category']
        image_url = request.form['image_url']

        c.execute('''UPDATE recipes 
                     SET title=?, ingredients=?, instructions=?, category=?, image_url=? 
                     WHERE id=? AND created_by=?''',
                  (title, ingredients, instructions, category, image_url, recipe_id, session['user_id']))
        conn.commit()
        conn.close()

        flash("Recipe updated successfully!", "success")
        return redirect(url_for('view_recipes'))

    # GET request → fetch the existing recipe data
    c.execute("SELECT * FROM recipes WHERE id=? AND created_by=?", (recipe_id, session['user_id']))
    recipe = c.fetchone()
    conn.close()

    if not recipe:
        flash("Recipe not found or unauthorized access.", "danger")
        return redirect(url_for('view_recipes'))

    return render_template('edit_recipe.html', recipe=recipe)


# ------------------------------------------------------------
# 🗑 DELETE RECIPE
# ------------------------------------------------------------
@app.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    """Deletes a recipe belonging to the logged-in user."""
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM recipes WHERE id=? AND created_by=?", (recipe_id, session['user_id']))
    conn.commit()
    conn.close()

    flash("Recipe deleted successfully!", "info")
    return redirect(url_for('view_recipes'))

# ------------------------------------------------------------
# 👁 VIEW SINGLE RECIPE (FULL DETAILS)
# ------------------------------------------------------------
@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    """Displays full details of a single recipe."""
    if 'user_id' not in session:
        flash("Please log in to view this recipe.", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM recipes WHERE id=? AND created_by=?", (recipe_id, session['user_id']))
    recipe = c.fetchone()
    conn.close()

    if not recipe:
        flash("Recipe not found or unauthorized access.", "danger")
        return redirect(url_for('view_recipes'))

    return render_template('View_RecipeInfo.html', recipe=recipe, username=session['username'])




# ------------------------------------------------------------
# 👑 ADMIN DASHBOARD
# ------------------------------------------------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    """Admin-only dashboard."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', username=session['username'])


# ------------------------------------------------------------
# 🚪 LOGOUT (USER)
# ------------------------------------------------------------
@app.route('/logoutuser')
def userLogout():
    """Logs out a normal user."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))


# ------------------------------------------------------------
# 🚪 LOGOUT (ADMIN)
# ------------------------------------------------------------
@app.route('/logoutadmin')
def adminLogout():
    """Logs out the admin."""
    session.clear()
    flash("Admin logged out successfully.", "info")
    return redirect(url_for('login'))


# ------------------------------------------------------------
# 🚀 RUN THE APP
# ------------------------------------------------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
