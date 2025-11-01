from app.models import Animal, AnimalType, User


def test_user_password_hashing(app):
    user = User(
        email="test@hash.com", first_name="Hash", last_name="User", user_type="user"
    )
    user.set_password("secret123")
    assert user.check_password("secret123")


def test_animal_creation(app, farmer_user):
    from app import db

    animal = Animal(
        name="Sheep A",
        animal_type=AnimalType.SHEEP,
        breed="Dorper",
        age=2,
        price=7000,
        farmer_id=farmer_user.id,
    )
    db.session.add(animal)
    db.session.commit()
    assert animal.name == "Sheep A"
