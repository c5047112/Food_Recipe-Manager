from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Import the separated DB connection
from db.db import get_db_connection

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------


# ---------------------------------------------
# INITIALIZE DATABASE AND DEFAULT ADMIN
# ---------------------------------------------


# USERS TABLE

# RECIPES TABLE



# REVIEWS TABLE



# Add default admin if it doesn't exist


# ---------------------------------------------
# HOME
# ---------------------------------------------
import random

@app.route("/")
def home():
    conn = get_db_connection()
    c = conn.cursor()

    # Get all approved recipes
    c.execute("SELECT * FROM recipes WHERE status='approved'")
    all_recipes = c.fetchall()

    # Pick random recipes for Featured (3) and Popular (6)
    featured_recipes = random.sample(all_recipes, min(3, len(all_recipes)))
    popular_recipes = random.sample(all_recipes, min(6, len(all_recipes)))

    # Stats
    c.execute("SELECT COUNT(*) AS total_recipes FROM recipes WHERE status='approved'")
    total_recipes = c.fetchone()["total_recipes"]

    c.execute("SELECT COUNT(*) AS total_users FROM users WHERE is_approved=1 AND is_admin=0")
    total_users = c.fetchone()["total_users"]

    c.execute("SELECT COUNT(*) AS total_chefs FROM users WHERE is_admin=1")
    total_chefs = c.fetchone()["total_chefs"]

    total_features = 50  # Hardcoded for demo

    # Example user stories
    user_stories = [
        {"name": "Priya Sharma", "role": "Home Chef", "story": "This app has made managing my recipes so easy! I love sharing them with friends and family.", "img": "https://randomuser.me/api/portraits/women/68.jpg"},
        {"name": "Rahul Verma", "role": "Food Blogger", "story": "Clean design and easy-to-use interface. Highly recommended for all food enthusiasts!", "img": "https://randomuser.me/api/portraits/men/45.jpg"},
        {"name": "Sneha Kapoor", "role": "Restaurant Owner", "story": "The admin tools are fantastic! Managing recipes has never been this smooth.", "img": "https://randomuser.me/api/portraits/women/22.jpg"},
    ]

    conn.close()

    return render_template(
        "index.html",
        featured_recipes=featured_recipes,
        popular_recipes=popular_recipes,
        total_recipes=total_recipes,
        total_users=total_users,
        total_chefs=total_chefs,
        total_features=total_features,
        user_stories=user_stories
    )


# ---------------------------------------------
# USER SIGNUP
# ---------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        c = conn.cursor()

        c.execute("""
            INSERT INTO users (username, email, password, is_approved, is_admin)
            VALUES (?, ?, ?, 0, 0)
        """, (username, email, password))

        conn.commit()
        conn.close()

        flash("Signup successful! Wait for admin approval.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------------------------------------
# LOGIN
# ---------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "user")  # Default role = user

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = user["is_admin"]

            if user["is_admin"] == 1:
                return redirect(url_for("admin_dashboard"))

            if user["is_approved"] == 0:
                flash("Admin approval required!", "danger")
                return redirect(url_for("login"))

            return redirect(url_for("user_dashboard"))

        flash("Invalid email or password!", "danger")

    return render_template("login.html", role=role)

# ---------------------------------------------
# LOGOUT
# ---------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------------------------------------
# USER DASHBOARD
# ---------------------------------------------
@app.route("/user_dashboard")
def user_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("user_dashboard.html", username=session["username"])

# ---------------------------------------------
# ADD RECIPE
# ---------------------------------------------
@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        ingredients = request.form["ingredients"]
        instructions = request.form["instructions"]
        category = request.form["category"]
        image_url = request.form["image_url"]
        video_url = request.form["video_url"]

        conn = get_db_connection()
        c = conn.cursor()

        c.execute("""
    INSERT INTO recipes 
    (title, ingredients, instructions, category, image_url, video_url, user_id, delete_request, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'pending')
    """, (title, ingredients, instructions, category,
      image_url, video_url, session["user_id"]))


        conn.commit()
        conn.close()

        flash("✅ Recipe submitted! Waiting for admin approval.", "info")
        return redirect(url_for("view_recipes"))

    return render_template("add_recipe.html", username=session["username"])

# ---------------------------------------------
# ✅ UPDATED — VIEW ALL RECIPES FOR ALL USERS
# ---------------------------------------------
# ---------------------------------------------------
# ✅ VIEW ALL RECIPES PAGE
@app.route("/view_recipes")
def view_recipes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
    SELECT recipes.*, users.username
    FROM recipes
    JOIN users ON recipes.user_id = users.id
    WHERE recipes.status = 'approved'
    """)

    recipes = c.fetchall()

    conn.close()

    return render_template(
        "view_recipes.html",
        recipes=recipes,
        username=session.get("username")
    )


# ---------------------------------------------------
# ✅ VIEW SINGLE RECIPE WITH CREATOR + REVIEWS
@app.route("/recipe/<int:recipe_id>")
def view_recipe(recipe_id):
    conn = get_db_connection()
    c = conn.cursor()

    # ✅ Fetch recipe + creator username
    c.execute("""
        SELECT recipes.*, users.username AS creator_username
        FROM recipes
        LEFT JOIN users ON recipes.user_id = users.id
        WHERE recipes.id = ?
    """, (recipe_id,))
    recipe = c.fetchone()

    # ✅ Fetch reviews + reviewer username
    c.execute("""
        SELECT reviews.*, users.username AS reviewer_username
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE recipe_id = ?
        ORDER BY created_at DESC
    """, (recipe_id,))
    reviews = c.fetchall()

    # ✅ Get avg rating + count
    c.execute("""
        SELECT 
            ROUND(AVG(rating), 1) AS avg_rating,
            COUNT(*) AS total_reviews
        FROM reviews
        WHERE recipe_id = ?
    """, (recipe_id,))
    rating_data = c.fetchone()

    avg_rating = rating_data["avg_rating"] or 0
    total_reviews = rating_data["total_reviews"]

    conn.close()

    return render_template(
        "view_RecipeInfo.html",
        recipe=recipe,
        username=session.get("username"),
        reviews=reviews,
        avg_rating=avg_rating,
        total_reviews=total_reviews
    )


@app.route("/recipe/<int:recipe_id>/add_review", methods=["POST"])
def add_review(recipe_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    rating = request.form["rating"]
    comment = request.form.get("comment", "")

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO reviews (recipe_id, user_id, rating, comment)
        VALUES (?, ?, ?, ?)
    """, (recipe_id, session["user_id"], rating, comment))

    conn.commit()
    conn.close()

    flash("✅ Review added successfully!", "success")
    return redirect(url_for("view_recipe", recipe_id=recipe_id))


@app.route("/recipe/<int:recipe_id>/reviews")
def get_reviews(recipe_id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        SELECT reviews.*, users.username
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE recipe_id = ?
        ORDER BY created_at DESC
    """, (recipe_id,))

    reviews = c.fetchall()
    conn.close()

    return reviews



# ---------------------------------------------
# EDIT RECIPE
# ---------------------------------------------
@app.route("/edit_recipe/<int:recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    recipe = c.fetchone()

    if request.method == "POST":
        title = request.form["title"]
        ingredients = request.form["ingredients"]
        instructions = request.form["instructions"]
        category = request.form["category"]
        image_url = request.form["image_url"]
        video_url = request.form["video_url"]

        c.execute("""
            UPDATE recipes 
            SET title=?, ingredients=?, instructions=?, category=?, image_url=?, video_url=?
            WHERE id=?
        """, (title, ingredients, instructions, category, image_url, video_url, recipe_id))

        conn.commit()
        conn.close()

        flash("Recipe updated successfully!", "success")
        return redirect(url_for("view_recipes"))

    conn.close()
    return render_template("edit_recipe.html", recipe=recipe)

# ---------------------------------------------
# USER DELETE REQUEST
# ---------------------------------------------
@app.route("/delete_recipe/<int:recipe_id>", methods=["POST"])
def delete_recipe(recipe_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE recipes SET delete_request = 1
        WHERE id = ? AND user_id = ?
    """, (recipe_id, session["user_id"]))

    conn.commit()
    conn.close()
    flash("Delete request sent to admin!", "warning")
    return redirect(url_for("view_recipes"))

# ---------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect("/login")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT users.id, users.username, users.email,
               COUNT(recipes.id) AS recipe_count
        FROM users
        LEFT JOIN recipes ON users.id = recipes.user_id
        WHERE users.is_admin = 0
        GROUP BY users.id
    """)
    users = c.fetchall()
    conn.close()

    return render_template("admin_dashboard.html",
                           users=users,
                           username=session["username"])

@app.route("/admin_requests")
def admin_requests():
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect("/login")

    conn = get_db_connection()
    c = conn.cursor()

    # Pending user approvals
    c.execute("SELECT * FROM users WHERE is_approved = 0 AND is_admin = 0")
    pending_users = c.fetchall()

    # Pending delete requests
    c.execute("""
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.delete_request = 1
    """)
    pending_deletes = c.fetchall()

    # Pending recipe approval requests
    c.execute("""
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.status = 'pending'
    """)
    pending_recipes = c.fetchall()

    conn.close()

    return render_template(
        "admin_requests.html",
        pending_users=pending_users,
        pending_deletes=pending_deletes,
        pending_recipes=pending_recipes,
        username=session["username"]
    )


# ---------------------------------------------
# ADMIN APPROVE / REJECT USER
# ---------------------------------------------
@app.route("/admin/approve_user/<int:user_id>", methods=["POST"])
def admin_approve_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET is_approved = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("User approved!", "success")
    return redirect(url_for("admin_requests"))

@app.route("/admin/reject_user/<int:user_id>", methods=["POST"])
def admin_reject_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("User rejected!", "danger")
    return redirect(url_for("admin_requests"))

# ---------------------------------------------
# ADMIN APPROVE / REJECT DELETE
# ---------------------------------------------
@app.route("/admin/approve_delete/<int:recipe_id>", methods=["POST"])
def admin_approve_delete(recipe_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

    flash("Recipe deleted!", "danger")
    return redirect(url_for("admin_requests"))

@app.route("/admin/reject_delete/<int:recipe_id>", methods=["POST"])
def admin_reject_delete(recipe_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE recipes SET delete_request = 0 WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

    flash("Delete request rejected!", "info")
    return redirect(url_for("admin_requests"))

# ---------------------------------------------
# ADMIN GET USER RECIPES
# ---------------------------------------------
@app.route("/admin/get_user_recipes/<int:user_id>")
def admin_get_user_recipes(user_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return {"error": "Unauthorized"}, 403

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, category
        FROM recipes
        WHERE user_id = ?
    """, (user_id,))
    recipes = c.fetchall()
    conn.close()

    return {"recipes": [
        {"id": r["id"], "title": r["title"], "category": r["category"]}
        for r in recipes
    ]}

@app.route("/admin/edit_user/<int:user_id>", methods=["GET", "POST"])
def admin_edit_user(user_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect(url_for("login"))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]

        c.execute("""
            UPDATE users SET username = ?, email = ?
            WHERE id = ?
        """, (username, email, user_id))

        conn.commit()
        conn.close()
        flash("User details updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    return render_template("admin_edit_user.html", user=user)

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect(url_for("login"))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully!", "danger")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_recipe/<int:recipe_id>", methods=["POST"])
def admin_delete_recipe(recipe_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect(url_for("login"))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

    flash("Recipe deleted successfully!", "danger")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/approve_recipe/<int:recipe_id>", methods=["POST"])
def admin_approve_recipe(recipe_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE recipes SET status = 'approved' WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

    flash("✅ Recipe approved successfully!", "success")
    return redirect(url_for("admin_requests"))


@app.route("/admin/reject_recipe/<int:recipe_id>", methods=["POST"])
def admin_reject_recipe(recipe_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

    flash("❌ Recipe rejected & removed!", "danger")
    return redirect(url_for("admin_requests"))


# ---------------------------------------------
# RUN APP
# ---------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
