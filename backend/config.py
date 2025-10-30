import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://username:password@localhost:5432/dbname'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get('JWT_ACCESS_TOKEN_HOURS', 168))  # Default 7 days
    )

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    # Ensure secrets are set in environment variables
    if 'SECRET_KEY' not in os.environ:
        raise ValueError("SECRET_KEY environment variable not set for production!")
    if 'JWT_SECRET_KEY' not in os.environ:
        raise ValueError("JWT_SECRET_KEY environment variable not set for production!")
    if 'DATABASE_URL' not in os.environ:
        raise ValueError("DATABASE_URL environment variable not set for production!")

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
