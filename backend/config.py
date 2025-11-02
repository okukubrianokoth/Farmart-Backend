import os
from datetime import timedelta
from dotenv import load_dotenv

# ✅ Load environment variables from .env if present
load_dotenv()

class Config:
    # 🔐 General App Config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 🗄️ Handle both SQLite (local) and PostgreSQL (Render)
    uri = os.environ.get('DATABASE_URL', 'sqlite:///farmart.db')
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = uri

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🔑 JWT Config
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # 💳 M-PESA API CONFIGURATION
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '0MGI4OURcyORSUN0BjmvzDW77r6dGyjRYcZdRYdbHLC20Xjl')
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '4UVbzIvUBoV5HxNFHDs3ZCSwsVuSFSDXRsWbSyiOEqB9NYtYZu60MZnpRC56rlZ8')

    # ✅ SHORTCODE AND PASSKEY
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '174379')
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')

    # 🌍 CALLBACK URL
    MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', 'https://coral-salamanderlike-ilona.ngrok-free.dev/api/payments/mpesa/callback')


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
