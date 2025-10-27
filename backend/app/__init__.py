from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize app and database
app = Flask(__name__)
db = SQLAlchemy(app)

# Import routes after app is created
from app import routes
