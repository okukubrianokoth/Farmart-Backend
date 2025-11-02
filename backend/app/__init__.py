# from flask import Flask
# from flask_bcrypt import Bcrypt
# from flask_cors import CORS
# from flask_jwt_extended import JWTManager
# from flask_migrate import Migrate
# from flask_sqlalchemy import SQLAlchemy

# # Initialize extensions
# db = SQLAlchemy()
# migrate = Migrate()
# jwt = JWTManager()
# bcrypt = Bcrypt()


# def create_app(config_name="default"):
#     """Application factory function"""
#     app = Flask(__name__)

#     # ✅ Load configuration
#     from config import config

#     app.config.from_object(config[config_name])

#     # ✅ Enable CORS (allow all origins in development)
#     CORS(app, supports_credentials=True)

#     # ✅ Initialize extensions
#     db.init_app(app)
#     migrate.init_app(app, db)
#     jwt.init_app(app)
#     bcrypt.init_app(app)

#     # ✅ Import models here to avoid circular imports
#     from app import models
#     from app.animals import animals_bp
#     # ✅ Register blueprints (ensure all routes are connected)
#     from app.auth import auth_bp
#     from app.cart import cart_bp
#     from app.orders import orders_bp
#     from app.payments import payments_bp  # <-- M-Pesa integration route

#     app.register_blueprint(auth_bp, url_prefix="/api/auth")
#     app.register_blueprint(animals_bp, url_prefix="/api")
#     app.register_blueprint(orders_bp, url_prefix="/api")
#     app.register_blueprint(cart_bp, url_prefix="/api")
#     app.register_blueprint(payments_bp, url_prefix="/api/payments")

#     print("✅ Flask app created successfully with blueprints registered.")
#     return app
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app(config_name="default"):
    """Application factory function"""
    app = Flask(__name__)

    # ✅ Load configuration from environment variables (for Render)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "superjwtsecret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///farmart.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ✅ Enable CORS
    CORS(app, supports_credentials=True)

    # ✅ Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # ✅ Import models to register them with SQLAlchemy
    from app import models

    # ✅ Import blueprints
    from app.animals import animals_bp
    from app.auth import auth_bp
    from app.cart import cart_bp
    from app.orders import orders_bp
    from app.payments import payments_bp  # M-Pesa

    # ✅ Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(animals_bp, url_prefix="/api")
    app.register_blueprint(orders_bp, url_prefix="/api")
    app.register_blueprint(cart_bp, url_prefix="/api")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")

    print("✅ Flask app created successfully with blueprints registered.")
    return app
