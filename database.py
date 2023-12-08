from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'database.db'

