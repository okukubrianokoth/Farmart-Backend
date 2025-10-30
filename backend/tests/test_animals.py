import unittest
from app import create_app, db
from app.models import User, Animal, UserType, AnimalType

class AnimalTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
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
            email='farmer@test.com',
            first_name='John',
            last_name='Doe',
            user_type=UserType.FARMER
        )
        farmer.set_password('password')
        db.session.add(farmer)
        db.session.commit()


