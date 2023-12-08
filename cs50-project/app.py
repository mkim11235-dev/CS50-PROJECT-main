import os
from flask import Flask, flash, render_template, request, redirect, url_for, session, g, jsonify, session, send_from_directory
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, EqualTo
import secrets
import math
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import time
import pytz



class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[InputRequired()])
    confirm = PasswordField('Repeat Password', validators=[InputRequired(), EqualTo('password')])

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = secrets.token_hex(32)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'runnify50@gmail.com'
app.config['MAIL_PASSWORD'] = 'ergtfb3c4tvb587tb)()T*&FG24rtcoi4nt3i'
app.config['MAIL_DEFAULT_SENDER'] = 'runnify50@gmail.com'

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'profile_pics')
PROFILE_PICS_FOLDER = os.path.join(os.path.dirname(__file__), 'profile_pics')

mail = Mail(app)



def get_db():
    db = sqlite3.connect('database.db')
    db.row_factory = sqlite3.Row  # This enables column access by name: row['column_name']
    return db

def calculate_distance(lat1, lon1, lat2, lon2):
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)
    # Haversine formula to calculate distance between two points on the Earth
    R = 6371  # Radius of the Earth in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

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


def get_published_time(time, now=None):
    # Convert the string to a datetime object (if not already a datetime object)
    if isinstance(time, str):
        published_time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    else:
        published_time = time

    published_time = pytz.utc.localize(published_time)

    # If now is not provided, use the current time
    if now is None:
        now = datetime.utcnow().replace(tzinfo=pytz.utc)

    time_difference = now - published_time

    days = time_difference.days
    seconds = time_difference.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return f"{days}d"
    elif hours > 0:
        return f"{hours}h"
    elif minutes > 0:
        return f"{minutes}min"
    else:
        return "Just now"

#Login function
@app.route("/login", methods=["POST","GET"])
def handle_login():

    if request.method == "POST":
        
        #Fetch the username and password from the template
        username = request.form.get("username")
        password = request.form.get("password")

        #If one of the fields is blank
        if not username or not password:
            
            #handle error
            return render_template("login.html", error="Must provide username and/or password"), 403

        # Query database for user corresponding to the one entered
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        # Ensure username exists and password is correct
        if not user or not check_password_hash(user[2], password): 
            
            return render_template("login.html", error="Invalid username and/or password"), 403

        # Remember which user has logged in
        session["user_id"] = user[0]
        session.permanent = True
        
        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")

#Logout function
@app.route("/logout")
def logout():
    
    #Log user out
    session.clear()
    return redirect("/")

#register function
@app.route("/register", methods=["POST","GET"])
def register():
    
    #Clear the session to avoid errors
    session.clear()

    if request.method == "POST":
        
        #Fetch variables from the template
        username = request.form.get("username")
        email = request.form.get ("email")
        password = request.form.get("password")
        confirmation=request.form.get("confirmation")

        #If one of the fields is blank
        if not username or not password or not confirmation or not email:
            
            #handle error
            return render_template("register.html", error="Must fill out all the fields"), 400

        cursor = get_db().cursor()
        #see if ther's a user with the same username
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        #if the user already exists
        if existing_user:
            #handle error
            return render_template("register.html", error="Username already exists"), 400
        
        #If the password and the confirmation are not the same
        if confirmation != password:
            
            #handle error
            return render_template("register.html",error="Passwords do not match")
        

        # Check the length of the password
        if len(password) < 8:
            #handle error
            return render_template("register.html", error="Password must at least be 8 characters long"), 400

        # Check for uppercase and lowercase letters
        if not any(char.isupper() for char in password) or not any(char.islower() for char in password):
            #handle error
            return render_template("register.html", error="Password must contain both upper case and lower case characters"), 400

        # Check for at least one digit
        if not any(char.isdigit() for char in password):
            #handle error
            return render_template("register.html", error="Password must contain digits"), 400

        # Check for at least one special character
        special_characters = "!@#$%^&*()-_+=<>?/[]{},.:;"
        if not any(char in special_characters for char in password):
            #handle error
            return render_template("register.html", error="Password must contain special characters"), 400

        #hash the password for maximum security
        hashed_password = generate_password_hash(password)
        
        # Insert new user into the database
        cursor.execute("INSERT INTO users (username, password, email, points) VALUES (?, ?,?,?)", (username, hashed_password, email, 20))
        get_db().commit()

        # Now, automatically log in the newly registered user
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        new_user = cursor.fetchone()

        # Set the session information for the logged-in user
        session["user_id"] = new_user[0]

        # Redirect to the home page after registration
        return redirect('/')

    else:
        return render_template("register.html")
    

# Route for handling forgot password requests
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    # Create an instance of the ForgotPasswordForm
    form = ForgotPasswordForm()

    # Check if the form is submitted and valid
    if form.validate_on_submit():
        # Retrieve email from the form
        email = form.email.data

        # Connect to the database
        db = get_db()
        cursor = db.cursor()

        # Check if there is a user with the given email
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            # Generate a reset token and set its expiry time
            token = secrets.token_hex(16)
            expiry = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
            cursor.execute("UPDATE users SET reset_token = ?, token_expiry = ? WHERE id = ?", (token, expiry, user[0]))
            db.commit()

            # Send an email with the reset instructions
            msg = Message('Password Reset Request', sender='your_email', recipients=[email])
            msg.body = f'''To reset your password, visit the following link:
            {url_for('reset_password', token=token, _external=True)}
            If you did not make this request, simply ignore this email and no changes will be made.
            '''
            mail.send(msg)

            # Inform the user and redirect to login
            flash('An email has been sent with instructions to reset your password.')
            return redirect(url_for('login'))
        else:
            # Inform the user about the invalid email
            flash('No account with that email. Please try again.')

    # Render the forgot_password.html template with the form
    return render_template('forgot_password.html', form=form)


# Route for handling password reset
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Create an instance of the ResetPasswordForm
    form = ResetPasswordForm()

    # Check if the form is submitted and valid
    if form.validate_on_submit():
        # Connect to the database
        db = get_db()
        cursor = db.cursor()

        # Check if the reset token is valid and has not expired
        cursor.execute("SELECT id FROM users WHERE reset_token = ? AND token_expiry > ?", (token, datetime.now()))
        user = cursor.fetchone()

        if user:
            # Generate a new password hash and update the user's password
            new_password = generate_password_hash(form.password.data)
            cursor.execute("UPDATE users SET password = ?, reset_token = NULL, token_expiry = NULL WHERE id = ?", (new_password, user[0]))
            db.commit()

            # Inform the user and redirect to login
            flash('Your password has been updated.')
            return redirect(url_for('login'))
        else:
            # Inform the user about the invalid or expired reset token
            flash('This reset token is invalid or has expired.')
            return redirect(url_for('forgot_password'))

    # Render the reset_password.html template with the form and token
    return render_template('reset_password.html', form=form, token=token)


@app.route("/")
def home():
    #if user is not logged in, redirect to the login page
    if "user_id" not in session:
        return redirect("/login")
    #else redirect to feed
    else:
        return redirect("/feed")

#show the feed of pending errands
@app.route("/feed", methods=["GET", "POST"])
def feed():
    # Query database for pending errands
    cursor = get_db().cursor()
    cursor.execute("""
        SELECT
            errands.id,  
            errands.title,
            users.username,
            errands.content,
            CAST((julianday('now') - julianday(errands.time)) AS INTEGER) AS days,
            CAST(((julianday('now') - julianday(errands.time)) * 24) AS INTEGER) % 24 AS hours,
            CAST(((julianday('now') - julianday(errands.time)) * 24 * 60) % 60 AS INTEGER) AS minutes,
            users.profile_picture_filename
        FROM errands
        JOIN users ON errands.user_id = users.id
        WHERE errands.status = 'pending'
        ORDER BY julianday('now') - julianday(errands.time) ASC
    """)
    rows = cursor.fetchall()
    return render_template("feed.html", rows=rows)

#Show nearby errands
@app.route('/nearby_errands', methods=['POST'])
def nearby_errands():
    
    #fetch the location data of the user
    data = request.get_json()
    user_latitude = float(data['latitude'])
    user_longitude = float(data['longitude'])

    # Fetch all errands from the database
    cursor = get_db().cursor()
    cursor.execute("""
        SELECT 
            errands.id, 
            errands.title, 
            errands.content, 
            errands.latitude, 
            errands.longitude,
            users.username,
            users.profile_picture_filename,
            CAST((julianday('now') - julianday(errands.time)) AS INTEGER) AS days_difference,
            CAST((julianday('now') - julianday(errands.time)) AS INTEGER) % 24 AS hours_difference,
            CAST(((julianday('now') - julianday(errands.time)) * 24 * 60) % 60 AS INTEGER) AS total_minutes_difference,
            errands.status
        FROM errands 
        JOIN users ON errands.user_id = users.id
        WHERE status = 'pending'
    """)

    rows = cursor.fetchall()

    # Calculate distance for each errand and sort
    sorted_errands = []
    for errand in rows:
        (
            errand_id,
            title, 
            content, 
            latitude, 
            longitude, 
            username, 
            profile_picture_filename, 
            days_difference, 
            hours_difference, 
            total_minutes_difference, 
            status
        ) = errand
        
        if latitude is not None and longitude is not None:
            distance = calculate_distance(user_latitude, user_longitude, latitude, longitude)
            sorted_errands.append({
                'id': errand_id,
                'title': title,
                'content': content,
                'distance': distance,
                'username': username,
                'profile_picture_filename': profile_picture_filename,
                'days_difference': days_difference,
                'hours_difference': hours_difference,
                'total_minutes_difference': total_minutes_difference,
                'status': status
            })
    

    sorted_errands.sort(key=lambda e: e['distance'])
    
    #return sorted errands
    return jsonify(sorted_errands)

#Display the errands being executed by the user in session
@app.route("/executing", methods=["POST","GET"])
def executing():
    #fetch the errands
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
            errands.id,
            errands.user_id,
            users.profile_picture_filename               
        FROM errands
        JOIN users ON errands.user_id = users.id
        WHERE errands.executer_id=? AND errands.status=?
    """, (session['user_id'], 'in progress',))

    rows = cursor.fetchall()
    cursor.close()
    
    #Fetch the publisher information
    cursor = get_db().cursor()
    cursor.execute("SELECT username , points, profile_picture_filename FROM users WHERE id=?",(session['user_id'],))
    user = cursor.fetchone()
 
    return render_template('profile.html', rows=rows, user=user)


#Display more details about the specific errand    
@app.route('/errand_detail/<int:errand_id>')
def errand_detail(errand_id):
    
    # Fetch errand's details from the database
    cursor = get_db().cursor()
    cursor.execute("""
        SELECT 
            e.id, 
            e.title, 
            e.content, 
            u.username,  
            e.status, 
            e.latitude, 
            e.longitude, 
            e.to_do_time, 
            e.user_id,
            e.time,
            e.executer_id
        FROM errands e
        JOIN users u ON e.user_id = u.id
        WHERE e.id = ?
    """, (errand_id,))
    errand = cursor.fetchone()

    # Check if errand is not None and has at least 10 elements
    if errand and len(errand) >= 10:
        # Pass the errand details to the template, including time difference
        return render_template('errand_detail.html', errand=errand, user_id=session["user_id"], get_published_time=get_published_time, time=errand[9])
    else:
        # Handle the case where errand or its elements are not found
        return "Errand not found or incomplete data", 404

#publish an errand
@app.route("/publish", methods=["POST", "GET"])
def publish():
    if request.method == "POST":
        
        #fetch data from the template
        title = request.form.get("title")
        content = request.form.get("content")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        duration = request.form.get("duration")

        # Convert duration to seconds before storing in the database
        duration_seconds = int(duration) * 60
        
        #fetch the user's points
        cursor = get_db().cursor()
        cursor.execute("SELECT points FROM users WHERE id=?", (session["user_id"],))
        points = cursor.fetchone()[0]

        #if the user has sufficient points
        if points >=5:
            #Update the points
            cursor.execute("UPDATE users SET points=? WHERE id=?", (points - 5, session["user_id"]))
            get_db().commit()
             
            # Insert new post into the database
            cursor.execute("INSERT INTO errands (user_id, title, content, time, status, latitude, longitude, to_do_time) VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending', ?, ?, ?)",
                (session["user_id"], title, content, latitude, longitude, duration_seconds))
            get_db().commit()
            
            #redirect to feed
            return redirect('/feed')
        else:
            #handle error
            return render_template('publish.html', error_message='Insufficient amount of points')
    else:
        return render_template("publish.html")
 
#execute an errand
@app.route('/execute_errand/<int:errand_id>')
def execute_errand(errand_id):
    
    #fetch the errand
    cursor=get_db().cursor()
    cursor.execute("""
        SELECT 
            e.id, 
            e.title, 
            e.content, 
            u.username, 
            e.time, 
            e.status, 
            e.latitude, 
            e.longitude, 
            e.to_do_time
        FROM errands e
        JOIN users u ON e.user_id = u.id
        WHERE e.id = ?
    """, (errand_id,))
    errand = cursor.fetchone()

    # Check if the errand is still pending 
    if errand[5]=='pending':
        
        # Update the status of the errand 
        cursor=get_db().cursor()
        cursor.execute("UPDATE errands SET status='in progress', executer_id=? WHERE id=?", (session['user_id'],errand_id,))
        get_db().commit()

        #Calculate the start time of the errand
        start_time=time.time()

        # redirect to the errand detail template
        return render_template('errand_detail.html', errand=errand, execution_result=True, start_time=start_time, get_published_time=get_published_time, time=errand[4])

    # Errand might have been already executed or not found
    return render_template('errand_detail.html', errand=errand, execution_result=False)

#Confirm that your errand has been executed by someone else
@app.route('/executed/<int:errand_id>')
def executed(errand_id):
    
    # Update the status of the errand
    cursor = get_db().cursor()
    cursor.execute("UPDATE errands SET status='executed' WHERE id=?", (errand_id,))
    get_db().commit()

    # Fetch the executer points
    cursor.execute("SELECT points FROM users JOIN errands ON users.id=errands.executer_id WHERE errands.id=?", (errand_id,))
    points = cursor.fetchone()

    # Update the executer's points
    cursor.execute("UPDATE users SET points=? WHERE id=(SELECT executer_id FROM errands WHERE id=?)", (points[0] + 5, errand_id))
    get_db().commit()
    
    #redirect to feed
    return redirect('/feed')

#opt out of the errand
@app.route('/opt_out/<int:errand_id>')
def opt_out(errand_id):
    
    #Update the status of the errand
    cursor=get_db().cursor()
    cursor.execute("UPDATE errands SET status='pending', executer_id=NULL  WHERE id=?",(errand_id,))
    get_db().commit()
    
    #redirerct to feed
    return redirect('/feed') 

#delete an errand
@app.route('/delete', methods=['POST'])
def delete():
    
    #fetch the errand's id
    id = request.form.get('id')

    #delete the errand corresponding to the id
    if id:
        cursor = get_db().cursor()
        cursor.execute("DELETE FROM errands WHERE id=?",(id,))
        get_db().commit()
        cursor.close()
    
    #redirect to profile
    return redirect('/profile') 

#access you profile
@app.route('/profile')
def profile():
    
    #fetch errands published by the user
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
        errands.id,
        errands.user_id               
    FROM errands
    JOIN users ON errands.user_id = users.id
    WHERE users.id = ?
    ORDER BY julianday('now') - julianday(errands.time) ASC""", (session['user_id'],))
    rows = cursor.fetchall()
    cursor.close()
    
    #get data about the user
    cursor = get_db().cursor()
    cursor.execute("SELECT username , points, profile_picture_filename FROM users WHERE id=?",(session['user_id'],))
    user = cursor.fetchone()

    #redirect to the profile html 
    return render_template('profile.html', rows=rows, user=user, user_id=session["user_id"])



# Upload profile picture to upload folder
@app.route('/profile_picture', methods=['POST'])
def profile_picture():

    if 'profile_picture' in request.files:
        
        # Retrieve the profile picture file from the request
        profile_picture = request.files['profile_picture']

        if profile_picture.filename != '':
            
            # Specify the folder where you want to save the uploaded files
            filename = secure_filename(profile_picture.filename)
            profile_picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save the uploaded profile picture to the server's upload folder
            profile_picture.save(profile_picture_path)

            # Update the user's profile picture filename in the database
            cursor = get_db().cursor()
            cursor.execute("UPDATE users SET profile_picture_filename = ? WHERE id = ?", (filename, session['user_id']))
            get_db().commit()

            # Redirect the user to their profile page after successful upload
            return redirect('/profile')

    # Return a message if no profile picture is uploaded
    return 'No profile picture uploaded'


# Grabbing profile picture from uploads
@app.route('/profile_pics/<filename>')
def fetch_profile_pic(filename):

    return send_from_directory(PROFILE_PICS_FOLDER, filename)

