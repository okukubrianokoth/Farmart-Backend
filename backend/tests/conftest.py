import pytest
from app import create_app, db
from app.models import User, UserType
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = create_app('default')
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def farmer_user(app):
    farmer = User(
        email="farmer@example.com",
        first_name="John",
        last_name="Farmer",
        user_type=UserType.FARMER
    )
    farmer.set_password("password123")
    db.session.add(farmer)
    db.session.commit()
    return farmer

@pytest.fixture
def normal_user(app):
    user = User(
        email="user@example.com",
        first_name="Jane",
        last_name="Doe",
        user_type=UserType.USER
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def auth_headers(app, farmer_user):
    token = create_access_token(identity=farmer_user.id)
    return {"Authorization": f"Bearer {token}"}
