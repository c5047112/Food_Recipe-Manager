from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("recipe.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------
# HOME
# ---------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


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

    return render_template("signup.html")


# ---------------------------------------------
# LOGIN
# ---------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
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

            # Admin login
            if user["is_admin"] == 1:
                return redirect(url_for("admin_dashboard"))

            # Normal user but not approved yet
            if user["is_approved"] == 0:
                flash("Admin approval required!", "danger")
                return redirect(url_for("login"))

            return redirect(url_for("user_dashboard"))

        flash("Invalid email or password!", "danger")

    return render_template("login.html")


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

        conn = get_db_connection()
        c = conn.cursor()

        c.execute("""
            INSERT INTO recipes 
            (title, ingredients, instructions, category, image_url, user_id, delete_request)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (title, ingredients, instructions, category, image_url, session["user_id"]))

        conn.commit()
        conn.close()

        flash("Recipe added successfully!", "success")
        return redirect(url_for("view_recipes"))

    return render_template("add_recipe.html", username=session["username"])


# ---------------------------------------------
# VIEW USER RECIPES
# ---------------------------------------------
@app.route("/view_recipes")
def view_recipes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    c = conn.cursor()

    # USER SHOULD SEE ALL RECIPES EVEN IF delete_request = 1
    c.execute("SELECT * FROM recipes WHERE user_id = ?", (session["user_id"],))
    recipes = c.fetchall()

    conn.close()

    return render_template("view_recipes.html",
                           recipes=recipes,
                           username=session["username"])


# ---------------------------------------------
# VIEW SINGLE RECIPE
# ---------------------------------------------
@app.route("/recipe/<int:recipe_id>")
def view_recipe(recipe_id):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    recipe = c.fetchone()

    conn.close()

    return render_template("view_recipe.html",
                           recipe=recipe,
                           username=session.get("username"))


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

        c.execute("""
            UPDATE recipes 
            SET title=?, ingredients=?, instructions=?, category=?, image_url=?
            WHERE id=?
        """, (title, ingredients, instructions, category, image_url, recipe_id))

        conn.commit()
        conn.close()

        flash("Recipe updated successfully!", "success")
        return redirect(url_for("view_recipes"))

    conn.close()
    return render_template("edit.html", recipe=recipe)


# ==========================================================
# USER DELETE REQUEST (NOT REAL DELETE)
# ==========================================================
@app.route("/delete_recipe/<int:recipe_id>", methods=["POST"])
def delete_recipe(recipe_id):
    """User sends delete request, recipe not deleted yet"""
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


# ==========================================================
# ADMIN DASHBOARD (SHOW ALL USERS & RECIPES COUNT)
# ==========================================================
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


# ==========================================================
# ADMIN REQUESTS PAGE 
# ==========================================================
@app.route("/admin_requests")
def admin_requests():
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect("/login")

    conn = get_db_connection()
    c = conn.cursor()

    # Users waiting for approval
    c.execute("SELECT * FROM users WHERE is_approved = 0 AND is_admin = 0")
    pending_users = c.fetchall()

    # Recipes marked for delete
    c.execute("""
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE delete_request = 1
    """)
    pending_deletes = c.fetchall()

    conn.close()

    return render_template("admin_requests.html",
                           pending_users=pending_users,
                           pending_deletes=pending_deletes,
                           username=session["username"])


# ==========================================================
# ADMIN: APPROVE / REJECT USER
# ==========================================================
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


# ==========================================================
# ADMIN: DELETE RECIPE APPROVAL
# ==========================================================
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


# ==========================================================
# ADMIN: GET RECIPES OF A USER
# ==========================================================
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


# ---------------------------------------------
# RUN APP
# ---------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
