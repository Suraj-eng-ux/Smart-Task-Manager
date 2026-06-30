from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Task

app = Flask(__name__)
app.config.from_object(Config)

# ---------------- DATABASE ----------------

db.init_app(app)

# ---------------- LOGIN MANAGER ----------------

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------- HOME ----------------

@app.route("/")
def home():
    return redirect(url_for("dashboard"))


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user:
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful! Please Login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            flash("Login Successful!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password!", "danger")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully!", "info")

    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():

    tasks = Task.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "dashboard.html",
        tasks=tasks
    )


# ---------------- ADD TASK ----------------

@app.route("/add-task", methods=["GET", "POST"])
@login_required
def add_task():

    if request.method == "POST":

        new_task = Task(
            title=request.form["title"],
            description=request.form["description"],
            priority=request.form["priority"],
            due_date=request.form["due_date"],
            user_id=current_user.id
        )

        db.session.add(new_task)
        db.session.commit()

        flash("Task Added Successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_task.html")


# ---------------- EDIT TASK ----------------

@app.route("/edit-task/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):

    task = Task.query.get_or_404(id)

    # Prevent editing another user's task
    if task.user_id != current_user.id:
        flash("Unauthorized Access!", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        task.title = request.form["title"]
        task.description = request.form["description"]
        task.priority = request.form["priority"]
        task.status = request.form["status"]
        task.due_date = request.form["due_date"]

        db.session.commit()

        flash("Task Updated Successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("edit_task.html", task=task)


# ---------------- DELETE TASK ----------------

@app.route("/delete-task/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    # Prevent deleting another user's task
    if task.user_id != current_user.id:
        flash("Unauthorized Access!", "danger")
        return redirect(url_for("dashboard"))

    db.session.delete(task)
    db.session.commit()

    flash("Task Deleted Successfully!", "success")

    return redirect(url_for("dashboard"))


# ---------------- MAIN ----------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)