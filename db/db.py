import sqlite3



DB_NAME = "recipe.db"
import os
print("Using DB file:", os.path.abspath(DB_NAME))


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------
# HOME PAGE QUERIES
# ---------------------------------------------

def get_approved_recipes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE status = 'approved'")
    recipes = cur.fetchall()
    conn.close()
    return recipes


def get_total_approved_recipes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM recipes WHERE status = 'approved'")
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_total_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM users
        WHERE is_approved = 1 AND is_admin = 0
    """)
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_total_admins():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count

def create_user(username, email, password):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (username, email, password, is_approved, is_admin)
        VALUES (?, ?, ?, 0, 0)
    """, (username, email, password))

    conn.commit()
    conn.close()

def get_user_by_email(email):
    """
    Fetch a single user by email.
    Returns a dict-like row if found, else None.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()
    return user

def add_recipe(title, ingredients, instructions, category, image_url, video_url, user_id):
    """
    Insert a new recipe into the database.
    The recipe will be marked as pending by default.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO recipes 
        (title, ingredients, instructions, category, image_url, video_url, user_id, delete_request, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'pending')
    """, (title, ingredients, instructions, category, image_url, video_url, user_id))
    conn.commit()
    conn.close()

def get_approved_recipes_with_user():
    """
    Fetch all approved recipes along with the username of the user who submitted them.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.status = 'approved'
    """)
    recipes = cur.fetchall()
    conn.close()
    return recipes

def get_recipe_by_id(recipe_id):
    """
    Fetch a single recipe along with the creator's username.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT recipes.*, users.username AS creator_username
        FROM recipes
        LEFT JOIN users ON recipes.user_id = users.id
        WHERE recipes.id = ?
    """, (recipe_id,))
    recipe = cur.fetchone()
    conn.close()
    return recipe


def get_reviews_by_recipe(recipe_id):
    """
    Fetch all reviews for a recipe along with the reviewer's username.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT reviews.*, users.username AS reviewer_username
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE recipe_id = ?
        ORDER BY created_at DESC
    """, (recipe_id,))
    reviews = cur.fetchall()
    conn.close()
    return reviews


def get_rating_data(recipe_id):
    """
    Fetch average rating and total review count for a recipe.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            ROUND(AVG(rating), 1) AS avg_rating,
            COUNT(*) AS total_reviews
        FROM reviews
        WHERE recipe_id = ?
    """, (recipe_id,))
    data = cur.fetchone()
    conn.close()
    return data

def add_review(recipe_id, user_id, rating, comment=""):
    """
    Insert a review for a recipe.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reviews (recipe_id, user_id, rating, comment)
        VALUES (?, ?, ?, ?)
    """, (recipe_id, user_id, rating, comment))
    conn.commit()
    conn.close()

def get_recipe_reviews(recipe_id):
    """
    Fetch all reviews for a given recipe with reviewer username.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT reviews.*, users.username AS reviewer_username
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE recipe_id = ?
        ORDER BY created_at DESC
    """, (recipe_id,))
    reviews = cur.fetchall()
    conn.close()
    return reviews

# Fetch a single recipe by ID
def get_recipe_by_id(recipe_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    recipe = cur.fetchone()
    conn.close()
    return recipe

# Update a recipe
def update_recipe(recipe_id, title, ingredients, instructions, category, image_url, video_url):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE recipes
        SET title=?, ingredients=?, instructions=?, category=?, image_url=?, video_url=?
        WHERE id=?
    """, (title, ingredients, instructions, category, image_url, video_url, recipe_id))
    conn.commit()
    conn.close()


def get_all_users_with_recipe_count():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT users.id, users.username, users.email,
               COUNT(recipes.id) AS recipe_count
        FROM users
        LEFT JOIN recipes ON users.id = recipes.user_id
        WHERE users.is_admin = 0
        GROUP BY users.id
    """)
    users = cur.fetchall()
    conn.close()
    return users

# Get all pending user approvals
def get_pending_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE is_approved = 0 AND is_admin = 0")
    users = cur.fetchall()
    conn.close()
    return users


# Get all pending recipe approval requests
def get_pending_recipes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.status = 'pending'
    """)
    recipes = cur.fetchall()
    conn.close()
    return recipes

def approve_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_approved = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def reject_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_user_recipes(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, category
        FROM recipes
        WHERE user_id = ?
    """, (user_id,))
    recipes = cur.fetchall()
    conn.close()
    return recipes

# Fetch single user by ID
def get_user_by_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

# Update user details
def update_user(user_id, username, email):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users 
        SET username = ?, email = ?
        WHERE id = ?
    """, (username, email, user_id))
    conn.commit()
    conn.close()

# Delete a user by ID
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# Delete a recipe by ID
def delete_recipe(recipe_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

# Approve a recipe by ID
def approve_recipe(recipe_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE recipes SET status = 'approved' WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

# Reject (delete) a recipe by ID
def reject_recipe(recipe_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

def update_user(user_id, username, email):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET username=?, email=? WHERE id=?", (username, email, user_id))
    conn.commit()
    conn.close()

# db/db.py

def get_user_by_id(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

# db/db.py

def get_recipes_by_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, category, status FROM recipes WHERE user_id = ?", (user_id,))
    recipes = c.fetchall()
    conn.close()
    return recipes


# Mark a recipe for delete request
def request_delete_recipe(recipe_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE recipes
        SET delete_request = 1
        WHERE id = ?
    """, (recipe_id,))
    conn.commit()
    conn.close()



# Get all recipes with pending delete requests
def get_pending_delete_requests():
    """
    Fetch all recipes that have pending delete requests along with username.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT recipes.id, recipes.title, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.delete_request = 1
    """)
    deletes = c.fetchall()
    conn.close()
    return deletes


# Approve delete request (Admin)
def approve_delete_recipe(recipe_id):
    """
    Admin approves delete request and removes recipe from DB.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()


# Reject delete request (Admin)
def reject_delete_request(recipe_id):
    """
    Admin rejects the delete request and resets delete_request = 0.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE recipes SET delete_request = 0 WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()


def get_approved_recipes_with_user():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        SELECT
            r.id,
            r.title,
            r.image_url,
            r.category,
            r.status,
            u.username AS creator_username,
            ROUND(AVG(rv.rating), 1) AS avg_rating,
            COUNT(rv.id) AS total_reviews
        FROM recipes r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN reviews rv ON r.id = rv.recipe_id
        WHERE r.status = 'approved'
        GROUP BY r.id
        ORDER BY r.id DESC
    """)

    recipes = c.fetchall()
    conn.close()
    return recipes
