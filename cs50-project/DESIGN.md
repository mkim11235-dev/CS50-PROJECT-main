This project was realized using VS Code and Github with the scripts: Flask, Python, SQLite3, Jinja, HTML, Javascript.

The data in this project was stored in two SQLite tables: 
-->users which has the following columns: id, username, password, email, points.
-The points are used as a currency in this app. To publish an errand, you have to spend 5 points and when you execute one, you gain 5 points back. Every user starts with 20 points so can publish up to 4 requests before they need to execute another person's request.
-->errands which has the following columns: id, status, time, latitude, longitude, to_do_time, executer_id.
-The status of the errand is one of three: 'pending' which means that nbo one is executing the errand, 'in progress' which means someone is in the process of executing it, and 'executed' which means that the errand has already been executed by someone
-The time column stores the time the errand has been  published in 
-latitude and longitude are coordinates the user provides on the map when publishing an errand to help the others execute it.
-To do time is an estimation of how long this errand is gonna take for a user to complete and is used for a timer that ensures the executer is actually doing the errand.
-executer_id stores the id of the person executing the errand.


The login and register routes are built on finance's routes and handle the login and registering of the user.
-->register function: for security reasons, the passwords are hashed before being stored using werkzeug.security's hash password and check password hash functions. Also, passwords must be at least 8 characters long, contain both upper and lower case characters, be a mix of numbers, letters, and symbols for maximum security. 
-->at the end of the login and register functions, the user id is stored into session["user_id"] for easy access afterwards

    change password function: User Requests Password Reset:
1. Password Reset Form: A form (`ForgotPasswordForm`) is provided where users can enter their email address to request a password reset.
2. Email Validation: The form validates the email address using WTForms validators, ensuring it's in the correct format.
3. Database Check: When the form is submitted, the application checks the database to see if a user exists with the provided email address.
    Generating and Storing a Reset Token:
1. Token Generation: If a user is found, a unique reset token is generated using `secrets.token`. This token is used to securely identify the password reset request.
2. Storing Token and Expiry**: The token, along with its expiry time, is stored in the user's record in the database.
Sending the Password Reset Email:
1. Email Composition: An email is composed using Flask-Mail, containing a message with a link for resetting the password. This link includes the generated token as a URL parameter.
2. Sending Email: The email is sent to the user's email address. The user is informed via a flash message that an email has been sent.
    User Resets Password:
1. Reset Password Page: When the user clicks the link in the email, they are directed to a reset password page (`ResetPasswordForm`), which includes fields for a new password and password confirmation.
2. Token Verification: The application verifies the token from the URL and checks its validity against the database (ensuring it hasn't expired).
3. Updating Password: If the token is valid, the user's new password (after hashing) replaces the old one in the database. The reset token is then cleared to prevent reuse.
-->Error Handling and Security:
- Invalid or Expired Token**: If the token is invalid or expired, the user is informed, and the password reset process is aborted.
- Email Not Found: If no account is associated with the provided email, the user is informed that no account was found.
- Secure Password Hashing: Passwords are hashed using `werkzeug.security.generate_password_hash` before storing in the database for security.
-->This implementation ensures a secure and user-friendly way for users to reset their passwords via email, with checks and validations at each step to maintain security and provide a good user experience.


There is a layout.html template which is a navbar built on finance's navbar that is linked to all templates and the design of it changes depending on wether the user is logged in or not.

The feed template shows the errands that have not been executed yet inside individual cards where information about the errands and it's publisher is shown. You can click on the cards to be redirected to the errand_detail template that depends on whether you are the one who published the errand or not. If you are the one who published it and ther's someone in the process of executing it, you can click o


Templates folder:
Database:
app.py:

# Define Flask forms for ForgotPassword and ResetPassword
class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[InputRequired()])
    confirm = PasswordField('Repeat Password', validators=[InputRequired(), EqualTo('password')])

# Initialize Flask application
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = secrets.token_hex(32)

# Configure Flask-Mail for sending email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'runnify50@gmail.com'
app.config['MAIL_PASSWORD'] = 'ergtfb3c4tvb587tb)()T*&FG24rtcoi4nt3i'
app.config['MAIL_DEFAULT_SENDER'] = 'runnify50@gmail.com'

# Configure file upload settings
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'profile_pics')
PROFILE_PICS_FOLDER = os.path.join(os.path.dirname(__file__), 'profile_pics')

# Initialize Flask-Mail
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

# Function to calculate distance between two geographical coordinates
def calculate_distance(lat1, lon1, lat2, lon2):
    # Haversine formula to calculate distance between two points on the Earth
    return distance

# Function to retrieve the current date and time
def julianday():
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_datetime

# Function to format and retrieve the time difference from the current time
def get_published_time(time, now=None):
    Purpose: Calculates the time difference between a given timestamp (time) and the current time (now).
    Functionality: Converts the timestamp to a datetime object, computes the difference from the current time, and formats it into a readable string like "3h ago" or "2d ago".
    return formatted_time_difference

# Login route
@app.route("/login", methods=["POST","GET"])
def handle_login():
    Route: @app.route("/login", methods=["POST","GET"])
    Purpose: Manages user login process.
    Functionality: Validates user credentials from the form data. If valid, it logs the user in and redirects to the home page; otherwise, it shows an error message.

# Logout route
@app.route("/logout")
def logout():
    Functionality: Clears the user session and redirects to the login page, effectively logging the user out.

# Registration route
@app.route("/register", methods=["POST","GET"])
def register():
    Functionality: Collects user information from the form, validates it, registers the user in the database, and redirects to the home page upon successful registration.

# Route for handling forgot password requests
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    Purpose: Allows users to request a password reset if they've forgotten their password.
    Functionality: Validates the submitted email, generates a reset token, sends an email with the reset link, and redirects to the login page.

# Route for handling password reset
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    Purpose: Facilitates resetting a user's password using a token.
    Functionality: Validates the reset token, allows the user to set a new password, updates the password in the database, and redirects to the login page.

# Home route
@app.route("/")
def home():
    Purpose: Serves as the home page of the application.
    Functionality: Checks if a user is logged in. If not, redirects to the login page. If logged in, redirects to the feed page showing pending errands.

# Feed route to display pending errands
@app.route("/feed", methods=["GET", "POST"])
def feed():
    Purpose: Displays a list of pending errands.
    Functionality: Retrieves and displays all pending errands from the database. The errands are shown in a feed-like format, typically sorted by the time they were posted.

# Nearby errands route
@app.route('/nearby_errands', methods=['POST'])
def nearby_errands():
    Purpose: Finds errands near the user's current location.
    Functionality: Receives the user's current geographical coordinates, calculates the distance of each errand from the user, and returns a list of errands sorted by proximity.

# Executing errands route
@app.route("/executing", methods=["POST","GET"])
def executing():
    Purpose: Manages the errands that a user is currently executing.
    Functionality: Retrieves and displays errands that the logged-in user has committed to execute. This includes details like errand title, description, location, the timer, and the time since it was posted.

# Errand detail route
@app.route('/errand_detail/<int:errand_id>')
def errand_detail(errand_id):
    Purpose: Displays detailed information about a specific errand.
    Functionality: Given an errand_id, this function fetches detailed information about the errand from the database, such as title, content, publisher's username, status, and location. It then renders a template to display these details, including the errand's location on a map if available.

# Publish errand route
@app.route("/publish", methods=["POST", "GET"])
def publish():
    Purpose: Allows users to publish new errands.
    Functionality: Handles both GET and POST requests. For GET requests, it simply renders the form to publish a new errand. For POST requests, it collects data from the form (like title, content, location, etc.), saves the new errand in the database, and redirects the user to the feed page.

# Execute errand route
@app.route('/execute_errand/<int:errand_id>')
def execute_errand(errand_id):
    Purpose: Enables users to commit to executing a specific errand.
    Functionality: When a user decides to execute an errand, this function updates the status of the errand in the database to 'in progress' and assigns the user as the executor. It then renders a page showing the details of the errand, including a timer or countdown if applicable.

# Confirm executed errand route
@app.route('/executed/<int:errand_id>')
def executed(errand_id):
    Purpose: Confirms the completion of an errand.
    Functionality: When a user confirms that an errand has been executed, this function updates the errand's status in the database to 'executed'. It also awards points to the user who executed the errand.

# Opt-out of errand route
@app.route('/opt_out/<int:errand_id>')
def opt_out(errand_id):
    Purpose: Allows a user to opt out of an errand they previously committed to execute.
    Functionality: This function is triggered when a user clicks the 'opt out' button on an errand detail page. It resets the errand's status to 'pending', making it available for others to execute.

# Delete errand route
@app.route('/delete', methods=['POST'])
def delete():
     Purpose: Deletes an errand from the database.
    Functionality: This function is called when the 'delete' button is clicked on a user's profile page. It removes the specified errand from the database.

# Profile route
@app.route('/profile')
def profile():
     Purpose: Displays the user's profile page.
     Functionality: Renders the profile.html template, showing errands published by the logged-in user. Users can view more details about their errands or delete them.

 
# Upload profile picture route
@app.route('/profile_picture', methods=['POST'])
def profile_picture():
     Purpose: Handles the uploading of a user's profile picture.
     Functionality: When a user uploads a profile picture, this function saves the image in a designated folder and updates the user's profile in the database with the filename of the uploaded image.

# Fetch profile picture route
@app.route('/profile_pics/<filename>')
def fetch_profile_pic(filename):
     Purpose: Retrieves a user's profile picture.
     Functionality: Fetches the specified profile picture from the server's storage to display it in various parts of the application, like the user's profile page or errand cards.


# Templates:

      layout.html: The base template that includes common elements like the navigation bar and the main structure used by other templates.

      login.html: The template for the login page where users enter their username and password.

      register.html: Used for new users to create an account by providing a username, email, password, and password confirmation.

      feed.html: Displays a feed of errands. It includes a list of errands with details like title, content, and time since posted.

      publish.html: A form for users to publish new errands, including fields for title, content, and location.
 
      profile.html: Shows the user's profile, including their posted errands and options to delete them or view more details.

      forgot_password.html: A form for users to request a password reset link if they've forgotten their password.

      reset_password.html: Allows users to reset their password using a token received via email.

      errand_detail.html: Displays detailed information about a specific errand, including options to execute or opt out of the errand.




