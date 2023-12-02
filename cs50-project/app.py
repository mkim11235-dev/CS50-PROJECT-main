from flask import Flask, flash, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress a warning
app.config['SECRET_KEY'] = secrets.token_hex(32)

db.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Errand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    users_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user = db.relationship('User', backref='errands', lazy=True)

@app.route("/")
def home():
    if session.get("user_id") is None:
        return render_template("login.html")
    else:
        return render_template('feed.html')


@app.route("/login", methods=["POST"])
def handle_login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "Must provide username and/or password", 403

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            return "Invalid username and/or password", 403

        session["user_id"] = user.id

        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

@app.route("/register", methods=["POST"])
def register():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("register.html", error="Must provide username and/or password"), 400

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            session["user_id"] = new_user.id
            return redirect("/")
        except:
            db.session.rollback()
            return render_template("register.html", error="Username already exists"), 400
    else:
        return render_template("register.html")

@app.route('/publish', methods=["POST", "GET"])
def publish():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        new_errand = Errand(users_id=session["user_id"], title=title, content=content)

        try:
            db.session.add(new_errand)
            db.session.commit()
            return redirect("/")
        except:
            db.session.rollback()
            return "Error while publishing", 500

    else:
        requests = Errand.query.all()
        return render_template("publish.html", requests=requests)
        
if __name__ == '__main__':
    with app.app_context():
        db.create_all()