from flask import Flask, g, render_template, redirect, request, session
import secrets
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# Function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('database.db')
    return db

# Function to close the database connection
def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Register the close_db function to be called when the application context ends
app.teardown_appcontext(close_db)

@app.route("/")
def home():
    if "user_id" not in session:
        return render_template("login.html")
    else:
        return render_template('feed.html')

@app.route("/login", methods=["POST","GET"])
def handle_login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            
            return render_template("login.html", error="Must provide username and/or password"), 403

        # Query database for username
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        # Ensure username exists and password is correct
        if not user or not check_password_hash(user[2], password): 
            
            return render_template("login.html", error="Invalid username and/or password"), 403

        # Remember which user has logged in
        session["user_id"] = user[0]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

@app.route("/register", methods=["POST","GET"])
def register():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation=request.form.get("confirmation")

        if not username or not password:
            
            return render_template("register.html", error="Must provide username and/or password"), 400

        hashed_password = generate_password_hash(password)

        # Check if username already exists
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            
            return render_template("register.html", error="Username already exists"), 400
        if confirmation != password:
            return render_template("register.html",error="Passwords do not match")
        
        # Insert new user into the database
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        get_db().commit()

        # Now, automatically log in the newly registered user
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        new_user = cursor.fetchone()

        # Set the session information for the logged-in user
        session["user_id"] = new_user[0]

        # Redirect to the home page or any other destination after registration
        return redirect('/')

    else:
        return render_template("register.html")

@app.route('/publish', methods=["POST", "GET"])
def publish():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        # Insert new post into the database
        cursor = get_db().cursor()
        cursor.execute("INSERT INTO errands (user_id, title, content) VALUES (?, ?, ?)",
                       (session["user_id"], title, content))
        get_db().commit()
        return redirect('/')
    else:
        return render_template("publish.html")