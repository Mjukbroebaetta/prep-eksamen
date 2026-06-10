import os
import sqlite3

from flask import Flask, g, redirect, render_template_string, request, send_from_directory, session, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "eksamen.db")
admin_pw = "admin"

app = Flask(__name__)
app.secret_key = "digitrade-secret-key"

def get_db_connection():
    """Return a SQLite connection for the current app context."""
    db = getattr(g, "_database", None)
    if db is None:
        db = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
        g._database = db
    return db


@app.teardown_appcontext
def close_db_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/", methods=["GET"])
def index():
    with open(os.path.join(BASE_DIR, "index.html"), "r", encoding="utf-8") as template_file:
        html = template_file.read()

    return render_template_string(
        html,
        logged_in_as=session.get("logged_in_as", "n/a"),
        auth_level=session.get("auth_level", session.get("auth", "n/a")),
    )


@app.route("/register", methods=["GET"])
def register_form():
    with open(os.path.join(BASE_DIR, "register.html"), "r", encoding="utf-8") as template_file:
        html = template_file.read()

    return render_template_string(
        html,
        logged_in_as=session.get("logged_in_as", "n/a"),
        auth=session.get("auth", session.get("auth_level", "n/a")),
    )


@app.route("/login", methods=["POST"])
def login():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        username = request.form.get("username")
        password = request.form.get("password")

        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        if cursor.fetchone() is None:
            return "Feil brukernavn eller passord", 403

        cursor.execute("SELECT auth FROM users WHERE username = ?", (username,))
        auth = cursor.fetchone()[0]

    session["logged_in_as"] = username
    session["auth"] = auth
    session["auth_level"] = auth

    if "logged_in_as" not in session:
        return redirect(url_for("index"))
    if auth_level := session.get("auth_level", session.get("auth", "n/a")) == 1 or session.get("auth_level", session.get("auth", "n/a")) == 2:

        with open(os.path.join(BASE_DIR, "loggedin_employee.html"), "r", encoding="utf-8") as template_file:
            html = template_file.read()

        return render_template_string(
            html,
            logged_in_as=session.get("logged_in_as", "n/a"),
            auth_level=session.get("auth_level", session.get("auth", "n/a")),
        )
    elif auth_level := session.get("auth_level", session.get("auth", "n/a")) == 0:

        with open(os.path.join(BASE_DIR, "loggedin_guest.html"), "r", encoding="utf-8") as template_file:
            html = template_file.read()

        return render_template_string(
            html,
            logged_in_as=session.get("logged_in_as", "n/a"),
            auth_level=session.get("auth_level", session.get("auth", "n/a")),
        )

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/register", methods=["POST"])
def register():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        username = request.form.get("username")
        password = request.form.get("password")
        auth = request.form.get("auth")

        if auth == "ansatt":
            admin_password = request.form.get("admin_password")
            auth_value = 1
            if admin_password != admin_pw:
                return "Feil admin-passord", 403
        else:
            auth_value = 0

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone() is not None:
            return "Brukernavn allerede i bruk", 403

        cursor.execute("INSERT INTO users (username, password, auth) VALUES (?, ?, ?)", (username, password, auth_value))
        conn.commit()

    return "OK", 200

@app.route("/ansatt")
def ansatt():
    if session.get("auth_level") not in (1, 2):
        return redirect(url_for("index"))

    with open(os.path.join(BASE_DIR, "loggedin_employee.html"), "r", encoding="utf-8") as template_file:
        html = template_file.read()

    return render_template_string(
        html,
        logged_in_as=session.get("logged_in_as", "n/a"),
        auth_level=session.get("auth_level", session.get("auth", "n/a")),
    )

@app.route("/gjest")
def gjest():
    if session.get("auth_level") != 0:
        return redirect(url_for("index"))

    with open(os.path.join(BASE_DIR, "loggedin_guest.html"), "r", encoding="utf-8") as template_file:
        html = template_file.read()

    return render_template_string(
        html,
        logged_in_as=session.get("logged_in_as", "n/a"),
        auth_level=session.get("auth_level", session.get("auth", "n/a")),
    )

#@app.route("/logged_in")
#def logged_in():



if __name__ == "__main__":
    app.run(debug=True)
