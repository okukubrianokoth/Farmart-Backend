import pytest

from app import create_app, db
from app.models import Animal, AnimalType, User, UserType


@pytest.fixture
def app():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def farmer_user(app):
    user = User(
        email="farmer@test.com",
        first_name="Farmer",
        last_name="Test",
        user_type=UserType.FARMER,
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def regular_user(app):
    user = User(
        email="user@test.com",
        first_name="User",
        last_name="Test",
        user_type=UserType.USER,
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user
