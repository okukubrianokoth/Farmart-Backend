import os
import cloudinary
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from app.uploads import upload_bp  # renamed to match clean upload blueprint

# ✅ Load environment variables early
load_dotenv()

# ✅ Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()


def create_app(config_name="default"):
    """Application factory function"""
    app = Flask(__name__)

    # ✅ Configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "superjwtsecret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///farmart.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ✅ Initialize extensions
    CORS(app, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # ✅ Configure Cloudinary (centralized setup)
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )

    # ✅ Import models and blueprints
    from app import models
    from app.animals import animals_bp
    from app.auth import auth_bp
    from app.cart import cart_bp
    from app.orders import orders_bp
    from app.payments import payments_bp

    # ✅ Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(animals_bp, url_prefix="/api")
    app.register_blueprint(orders_bp, url_prefix="/api")
    app.register_blueprint(cart_bp, url_prefix="/api")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")
    app.register_blueprint(upload_bp, url_prefix="/api")  # clean upload endpoint

    print("✅ Flask app created successfully with blueprints registered and Cloudinary configured.")
    return app
