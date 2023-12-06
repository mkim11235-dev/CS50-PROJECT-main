import os
from flask import Flask, flash, g, render_template, redirect, request, session
from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, EqualTo
import secrets
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename



class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[InputRequired()])
    confirm = PasswordField('Repeat Password', validators=[InputRequired(), EqualTo('password')])

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

def julianday():
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_datetime

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    else:
        return redirect("/feed")

@app.route("/feed", methods=["GET", "POST"])
def feed():
    # Query database for pending errands
    cursor = get_db().cursor()
    cursor.execute("""
        SELECT
            errands.id,  -- Include the errand ID
            errands.title,
            users.username,
            errands.content,
            CAST((julianday('now') - julianday(errands.time)) AS INTEGER) AS days_difference,
            CAST(((julianday('now') - julianday(errands.time)) * 24) AS INTEGER) % 24 AS hours_difference,
            CAST(((julianday('now') - julianday(errands.time)) * 24 * 60) % 60 AS INTEGER) AS total_minutes_difference
        FROM errands
        JOIN users ON errands.user_id = users.id
        WHERE errands.status = 'pending'
        ORDER BY errands.time DESC
    """)
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
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if user:
            token = secrets.token_hex(16)
            expiry = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
            cursor.execute("UPDATE users SET reset_token = ?, token_expiry = ? WHERE id = ?", (token, expiry, user[0]))
            db.commit()

            msg = Message('Password Reset Request', sender='your_email', recipients=[email])
            msg.body = f'''To reset your password, visit the following link:
{url_for('reset_password', token=token, _external=True)}
If you did not make this request, simply ignore this email and no changes will be made.
'''
            mail.send(msg)
            flash('An email has been sent with instructions to reset your password.')
            return redirect(url_for('login'))
        else:
            flash('No account with that email. Please try again.')
    return render_template('forgot_password.html', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE reset_token = ? AND token_expiry > ?", (token, datetime.now()))
        user = cursor.fetchone()
        if user:
            new_password = generate_password_hash(form.password.data)
            cursor.execute("UPDATE users SET password = ?, reset_token = NULL, token_expiry = NULL WHERE id = ?", (new_password, user[0]))
            db.commit()
            flash('Your password has been updated.')
            return redirect(url_for('login'))
        else:
            flash('This reset token is invalid or has expired.')
            return redirect(url_for('forgot_password'))
    return render_template('reset_password.html', form=form, token=token)


@app.route("/publish", methods=["POST", "GET"])
def publish():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        cursor = get_db().cursor()
        cursor.execute("INSERT INTO errands (user_id, title, content, time, status, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (session["user_id"], title, content, julianday(), 'pending', latitude, longitude))
        get_db().commit()
        return redirect('/feed')
    else:
        return render_template("publish.html")
    

    
@app.route('/errand/<int:errand_id>')
def view_errand(errand_id):
    # Fetch errand details from the database
    cursor = get_db().cursor()
    cursor.execute("""
        SELECT e.id, e.title, e.content, u.username, e.time, e.status, e.latitude, e.longitude
        FROM errands e
        JOIN users u ON e.user_id = u.id
        WHERE e.id = ?
    """, (errand_id,))
    errand = cursor.fetchone()

    if errand:
        # Pass the errand details to the template
        return render_template('errand_detail.html', errand=errand)
    else:
        # Handle the case where errand is not found
        return "Errand not found", 404
    
    
@app.route('/execute_errand/<int:errand_id>', methods=['GET', 'POST'])
def execute_errand(errand_id):
    # Add your logic for executing the errand here
    # For example, updating the errand status in the database

    # Redirect to an appropriate page after execution
    return redirect(url_for('feed'))

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
    cursor.execute("SELECT username , points, profile_picture_filename FROM users WHERE id=?",(session['user_id'],))
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
        filename = secure_filename(profile_picture.filename)
        profile_picture_path = os.path.join(upload_folder, filename)
        profile_picture.save(profile_picture_path)

        # Update the user's profile picture in the database
        cursor = get_db().cursor()
        cursor.execute("UPDATE users SET profile_picture_filename = ? WHERE id = ?", (filename, session['user_id']))
        get_db().commit()


        return redirect('/profile')

    return 'No profile picture uploaded'



    