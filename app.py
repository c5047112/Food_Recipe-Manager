from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Import the separated DB connection
from db.db import (
    get_approved_recipes,
    get_total_admins,
    get_total_approved_recipes,
    get_total_users,
    create_user,
    add_recipe,
    get_user_by_email,
    get_approved_recipes_with_user,
    get_rating_data,
    get_recipe_by_id,
    get_reviews_by_recipe,
    add_review,
    get_recipe_reviews,
    update_recipe,
    request_delete_recipe,
    get_all_users_with_recipe_count,
    get_pending_delete_requests,
    get_pending_recipes,
    get_pending_users,
    approve_user,
    reject_user,
    approve_delete_recipe,
    reject_delete_request,
    get_user_recipes,
    update_user,
    get_user_by_id,
    delete_user,
    delete_recipe,
    approve_recipe,
    reject_recipe,
    get_recipes_by_user,
)

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------------------------------------
# HOME
# ---------------------------------------------
import random
@app.route("/")
def home():
    all_recipes = get_approved_recipes()

    featured_recipes = random.sample(all_recipes, min(3, len(all_recipes)))
    popular_recipes = random.sample(all_recipes, min(6, len(all_recipes)))

    total_recipes = get_total_approved_recipes()
    total_users = get_total_users()
    total_chefs = get_total_admins()
    total_features = 50  # demo value

    user_stories = [
        {"name": "Priya Sharma", "role": "Home Chef", "story": "This app has made managing my recipes so easy!", "img": "https://randomuser.me/api/portraits/women/68.jpg"},
        {"name": "Rahul Verma", "role": "Food Blogger", "story": "Clean design and easy-to-use interface.", "img": "https://randomuser.me/api/portraits/men/45.jpg"},
        {"name": "Sneha Kapoor", "role": "Restaurant Owner", "story": "Admin tools are fantastic!", "img": "https://randomuser.me/api/portraits/women/22.jpg"},
    ]

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

import random
import smtplib
from email.message import EmailMessage

EMAIL_ADDRESS = "prithviroshan2003@gmail.com"
EMAIL_PASSWORD = "ivca waor kjne ydyf"

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    msg = EmailMessage()
    msg["Subject"] = "Verify Your Account - OTP"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(f"""
Hello,

Your OTP for account verification is: {otp}

This OTP is valid for 5 minutes.

Thank you!
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]

        # Check if the email already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            flash("❌ Email already exists! Please use a different email.", "danger")
            return render_template("register.html", username=request.form["username"], email=email)

        # If email doesn't exist, continue with OTP process
        session["signup_data"] = {
            "username": request.form["username"],
            "email": email,
            "password": generate_password_hash(request.form["password"])
        }

        otp = generate_otp()
        session["signup_otp"] = otp

        send_otp_email(email, otp)

        flash("OTP sent to your email!", "info")
        return redirect(url_for("verify_otp"))

    return render_template("register.html")



@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "signup_otp" not in session:
        return redirect(url_for("signup"))

    if request.method == "POST":
        user_otp = request.form["otp"]

        if user_otp == session["signup_otp"]:
            data = session["signup_data"]

            create_user(
                data["username"],
                data["email"],
                data["password"]
            )

            session.pop("signup_otp")
            session.pop("signup_data")

            flash("Account verified successfully! Wait for admin approval.", "success")
            return redirect(url_for("login"))

        flash("Invalid OTP. Try again!", "danger")

    return render_template("verify_otp.html")



# ---------------------------------------------
# LOGIN
# ---------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "user")  # Default role = user

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = get_user_by_email(email)  # Use DB method

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
def add_recipe_route():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        ingredients = request.form["ingredients"]
        instructions = request.form["instructions"]
        category = request.form["category"]
        image_url = request.form["image_url"]
        video_url = request.form["video_url"]

        add_recipe(title, ingredients, instructions, category, image_url, video_url, session["user_id"])

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

    recipes = get_approved_recipes_with_user()

    return render_template(
        "view_recipes.html",
        recipes=recipes,
        username=session.get("username")
    )

# ---------------------------------------------------
# ✅ VIEW SINGLE RECIPE WITH CREATOR + REVIEWS
@app.route("/recipe/<int:recipe_id>")
def view_recipe(recipe_id):
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        flash("Recipe not found!", "danger")
        return redirect(url_for("home"))

    reviews = get_reviews_by_recipe(recipe_id)
    rating_data = get_rating_data(recipe_id)

    avg_rating = rating_data["avg_rating"] or 0
    total_reviews = rating_data["total_reviews"]

    return render_template(
        "view_RecipeInfo.html",
        recipe=recipe,
        username=session.get("username"),
        reviews=reviews,
        avg_rating=avg_rating,
        total_reviews=total_reviews
    )


@app.route("/recipe/<int:recipe_id>/add_review", methods=["POST"])
def add_review_route(recipe_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    rating = request.form["rating"]
    comment = request.form.get("comment", "")

    add_review(recipe_id, session["user_id"], rating, comment)

    flash("✅ Review added successfully!", "success")
    return redirect(url_for("view_recipe", recipe_id=recipe_id))

@app.route("/recipe/<int:recipe_id>/reviews")
def get_reviews(recipe_id):
    reviews = get_recipe_reviews(recipe_id)
    return reviews

# ---------------------------------------------
# EDIT RECIPE
# ---------------------------------------------
@app.route("/edit_recipe/<int:recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    recipe = get_recipe_by_id(recipe_id)

    if request.method == "POST":
        title = request.form["title"]
        ingredients = request.form["ingredients"]
        instructions = request.form["instructions"]
        category = request.form["category"]
        image_url = request.form["image_url"]
        video_url = request.form["video_url"]

        update_recipe(recipe_id, title, ingredients, instructions, category, image_url, video_url)

        flash("Recipe updated successfully!", "success")
        return redirect(url_for("view_recipes"))

    return render_template("edit_recipe.html", recipe=recipe)

# ---------------------------------------------
# USER DELETE REQUEST
# ---------------------------------------------
# User requests recipe deletion
@app.route("/delete_recipe/<int:recipe_id>", methods=["POST"])
def delete_recipe(recipe_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only pass recipe_id now
    request_delete_recipe(recipe_id)

    flash("Delete request sent to admin!", "warning")
    return redirect(url_for("view_recipes"))


# ---------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect("/login")

    users = get_all_users_with_recipe_count()

    return render_template("admin_dashboard.html",
                           users=users,
                           username=session["username"])

@app.route("/admin_requests")
def admin_requests():
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect("/login")

    pending_users = get_pending_users()
    pending_deletes = get_pending_delete_requests()
    pending_recipes = get_pending_recipes()

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
    approve_user(user_id)
    flash("User approved!", "success")
    return redirect(url_for("admin_requests"))


@app.route("/admin/reject_user/<int:user_id>", methods=["POST"])
def admin_reject_user(user_id):
    reject_user(user_id)
    flash("User rejected!", "danger")
    return redirect(url_for("admin_requests"))

# ---------------------------------------------
# ADMIN APPROVE / REJECT DELETE
# ---------------------------------------------
# Admin approves delete request
@app.route("/admin/approve_delete/<int:recipe_id>", methods=["POST"])
def admin_approve_delete(recipe_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect(url_for("login"))

    approve_delete_recipe(recipe_id)
    flash("Recipe deleted successfully!", "danger")
    return redirect(url_for("admin_requests"))

# Admin rejects delete request
@app.route("/admin/reject_delete/<int:recipe_id>", methods=["POST"])
def admin_reject_delete(recipe_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect(url_for("login"))

    reject_delete_request(recipe_id)
    flash("Delete request rejected!", "info")
    return redirect(url_for("admin_requests"))

# ---------------------------------------------
# ADMIN GET USER RECIPES
# ---------------------------------------------
@app.route("/admin/get_user_recipes/<int:user_id>")
def admin_get_user_recipes(user_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return {"error": "Unauthorized"}, 403

    recipes = get_user_recipes(user_id)
    return {"recipes": [
        {"id": r["id"], "title": r["title"], "category": r["category"]}
        for r in recipes
    ]}


@app.route("/admin/edit_user/<int:user_id>", methods=["GET", "POST"])
def admin_edit_user(user_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]

        update_user(user_id, username, email)

        flash("User details updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_edit_user.html", user=user)

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect(url_for("login"))

    delete_user(user_id)
    flash("User deleted successfully!", "danger")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete_recipe/<int:recipe_id>", methods=["POST"])
def admin_delete_recipe(recipe_id):
    if "is_admin" not in session or session["is_admin"] != 1:
        return redirect(url_for("login"))

    delete_recipe(recipe_id)
    flash("Recipe deleted successfully!", "danger")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/approve_recipe/<int:recipe_id>", methods=["POST"])
def admin_approve_recipe(recipe_id):
    approve_recipe(recipe_id)
    flash("✅ Recipe approved successfully!", "success")
    return redirect(url_for("admin_requests"))


@app.route("/admin/reject_recipe/<int:recipe_id>", methods=["POST"])
def admin_reject_recipe(recipe_id):
    reject_recipe(recipe_id)
    flash("❌ Recipe rejected & removed!", "danger")
    return redirect(url_for("admin_requests"))


@app.route("/user/profile")
def user_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Fetch user info
    user = get_user_by_id(user_id)

    # Fetch user's recipes
    recipes = get_recipes_by_user(user_id)

    return render_template("user_profile.html", user=user, recipes=recipes)


@app.route("/user/edit", methods=["GET", "POST"])
def edit_user_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = get_user_by_id(user_id)  # <-- use DB helper

    if request.method == "POST":
        new_username = request.form["username"]
        new_email = request.form["email"]

        session["update_email"] = {"username": new_username, "email": new_email}

        # If email is changed, generate OTP
        if new_email != user["email"]:
            otp = generate_otp()
            session["email_otp"] = otp
            send_otp_email(new_email, otp)
            flash("OTP sent to your new email!", "info")
            return redirect(url_for("verify_email_otp"))

        # Update only username if email didn't change
        update_user(user_id, new_username, new_email)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("user_profile"))

    return render_template("edit_user_profile.html", user=user)


@app.route("/user/verify_email_otp", methods=["GET", "POST"])
def verify_email_otp():
    if "email_otp" not in session:
        return redirect(url_for("edit_user_profile"))

    if request.method == "POST":
        user_otp = request.form["otp"]
        if user_otp == session["email_otp"]:
            data = session["update_email"]
            update_user(session["user_id"], data["username"], data["email"])

            # Clear OTP sessions
            session.pop("email_otp")
            session.pop("update_email")
            flash("Email updated successfully!", "success")
            return redirect(url_for("user_profile"))

        flash("Invalid OTP!", "danger")

    return render_template("verify_email_otp.html")


@app.route("/user/my_recipes")
def view_user_recipes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Fetch recipes added by the logged-in user
    recipes = get_recipes_by_user(user_id)

    return render_template("user_recipes.html", recipes=recipes)


@app.route("/request_delete/<int:recipe_id>", methods=["POST"])
def request_delete(recipe_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Mark the recipe as having a pending delete request
    request_delete_recipe(recipe_id)
    
    flash("Delete request sent to admin!", "warning")
    return redirect(url_for("view_recipes"))  # or wherever your recipes are listed


# ---------------------------------------------
# RUN APP
# ---------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
