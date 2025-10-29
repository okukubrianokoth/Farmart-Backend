from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
bcrypt = Bcrypt()

def create_app(config_name='default'):
    app = Flask(__name__)

    # Import config
    from config import config
    app.config.from_object(config[config_name])

     #SIMPLE CORS FIX - Allow all for development
    CORS(APP)

    #initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init app(app)

    #Import models 
    from app import models

   