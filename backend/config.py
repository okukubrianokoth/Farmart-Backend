import os
from datetime import timedelta

class Config:
    # 🔐 General App Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///farmart.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🔑 JWT Config
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # 💳 M-PESA API CONFIGURATION
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY') or '0MGI4OURcyORSUN0BjmvzDW77r6dGyjRYcZdRYdbHLC20Xjl'
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET') or '4UVbzIvUBoV5HxNFHDs3ZCSwsVuSFSDXRsWbSyiOEqB9NYtYZu60MZnpRC56rlZ8'

    # ✅ SHORTCODE AND PASSKEY
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE') or '174379'
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY') or 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

    # 🌍 CALLBACK URL (ngrok public URL)
    MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL') or 'https://coral-salamanderlike-ilona.ngrok-free.dev/api/payments/mpesa/callback'


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
