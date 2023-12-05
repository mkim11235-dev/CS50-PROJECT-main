from flask import Flask, g, render_template, redirect, request, session
from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, EqualTo
import secrets
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'runnify50@gmail.com'
app.config['MAIL_PASSWORD'] = 'ergtfb3c4tvb587tb)()T*&FG24rtcoi4nt3i'
app.config['MAIL_DEFAULT_SENDER'] = 'runnify50@gmail.com'

mail = Mail(app)

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
        return redirect("/login")
    else:
        return redirect("/feed")

@app.route("/feed", methods=["GET","POST"])
def feed():
    
    # Query database for pending errands
    cursor = get_db().cursor()
    cursor.execute("""
        SELECT
        errands.title,
        users.username,
        errands.content,
        CAST((julianday('now') - julianday(errands.time)) AS INTEGER) AS days_difference,
        CAST(((julianday('now') - julianday(errands.time)) * 24 ) AS INTEGER) % 24 AS hours_difference,
        CAST(((julianday('now') - julianday(errands.time)) * 24 *60) % 60 AS INTEGER) AS total_minutes_difference
    FROM errands
    JOIN users ON errands.user_id = users.id
    WHERE errands.status = 'pending'
    ORDER BY errands.time DESC""");
    rows = cursor.fetchall()
    return render_template("feed.html", rows=rows)

@app.route("/login", methods=["POST","GET"])
def handle_login():

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
        email = request.form.get ("email")
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
        cursor.execute("INSERT INTO users (username, password, email, points) VALUES (?, ?,?,?)", (username, hashed_password, email, 20))
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
    

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            password_reset_token = secrets.token_hex(16)
            cursor.execute("UPDATE users SET password_reset_token = ? WHERE id = ?", (password_reset_token, user[0]))
            get_db().commit()

            reset_url = url_for('reset_password', token=password_reset_token, _external=True)
            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"To reset your password, visit the following link: {reset_url}"
            mail.send(msg)

        return render_template('forgot_password.html', message="If an account with that email was found, we've sent a reset link to it.")

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form.get('password')
        hashed_new_password = generate_password_hash(new_password)

        cursor = get_db().cursor()
        cursor.execute("UPDATE users SET password = ?, password_reset_token = NULL WHERE password_reset_token = ?", (hashed_new_password, token))
        get_db().commit()

        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


@app.route("/publish", methods=["POST", "GET"])
def publish():
    return render_template('publish.html')

    """if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        # Insert new post into the database
        cursor = get_db().cursor()
        cursor.execute("INSERT INTO errands (user_id, title, content, time, status) VALUES (?, ?, ?,?,?)",
                       (session["user_id"], title, content, julianday('now'),'pending'))
        get_db().commit()
        return redirect('/publish')
    else:
        return render_template("publish.html")"""
    

    
@app.route('/execute',methods=["POST","GET"])
def execute():
    return render_template("execute.html")

@app.route('/profile')
def profile():
    cursor = get_db().cursor()
    cursor.execute("""
        SELECT
        errands.title,
        users.username,
        errands.content,
        CAST((julianday('now') - julianday(errands.time)) AS INTEGER) AS days_difference,
        CAST(((julianday('now') - julianday(errands.time)) * 24 ) AS INTEGER) % 24 AS hours_difference,
        CAST(((julianday('now') - julianday(errands.time)) * 24 *60) % 60 AS INTEGER) AS total_minutes_difference,
        errands.status,
        errands.id
    FROM errands
    JOIN users ON errands.user_id = users.id
    WHERE users.id = ?
    ORDER BY errands.time DESC""", (session['user_id'],))
    rows = cursor.fetchall()
    cursor.close()
    
    cursor=get_db().cursor()
    cursor.execute("SELECT username , points FROM users WHERE id=?",(session['user_id'],))
    user=cursor.fetchall()
    return render_template('profile.html', rows=rows, user=user)

@app.route('/delete', methods=['POST'])
def delete():
    id = request.form.get('id')

    if id:
        cursor = get_db().cursor()
        cursor.execute("DELETE FROM errands WHERE id=?",(id,))
        get_db().commit()
        cursor.close()
    return redirect('/profile')

@app.route('/profile_picture', methods=['POST'])
def profile_picture():
    if 'profile_picture' in request.files:
        profile_picture = request.files['profile_picture']

        # Specify the folder where you want to save the uploaded files
        upload_folder = 'profile_pics/'
        profile_picture.save(os.path.join(upload_folder, 'profile_picture.jpg'))

        # You can also update the user's profile in the database if needed

        return 'Profile picture uploaded successfully'

    return 'No profile picture uploaded'

    