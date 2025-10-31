import unittest

from app import create_app, db
from app.models import Animal, AnimalType, User, UserType


class AnimalTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_animal(self):
        # Create farmer user
        farmer = User(
            email="farmer@test.com",
            first_name="John",
            last_name="Doe",
            user_type=UserType.FARMER,
        )
        farmer.set_password("password")
        db.session.add(farmer)
        db.session.commit()

        # Login
        login_response = self.client.post(
            "/auth/login", json={"email": "farmer@test.com", "password": "password"}
        )
        token = login_response.get_json()["access_token"]

        # Add animal
        response = self.client.post(
            "/animals",
            json={
                "name": "Test Cow",
                "animal_type": "cattle",
                "breed": "Angus",
                "age": 24,
                "price": 1500.00,
                "weight": 500.00,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("Animal added successfully", response.get_json()["message"])
