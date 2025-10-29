from app import create_app, db
from app.models import User, Animal, UserType, AnimalType

app = create_app('default')

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Create a sample farmer user
    farmer = User(
        email='farmer@example.com',
        first_name='John',
        last_name='Doe',
        user_type=UserType.FARMER,
        phone='+1234567890',
        address='123 Farm Street, Farmville'
    )
    farmer.set_password('password123')
    
    # Create a sample regular user
    user = User(
        email='user@example.com',
        first_name='Jane',
        last_name='Smith',
        user_type=UserType.USER,
        phone='+0987654321',
        address='456 City Road, Cityville'
    )
    user.set_password('password123')
    
    # Add sample animals
    animals = [
        Animal(
            name='Bessie the Cow',
            animal_type=AnimalType.CATTLE,
            breed='Angus',
            age=24,
            price=1500.00,
            weight=500.00,
            description='Healthy Angus cow, 2 years old, ready for breeding.',
            image_url='https://via.placeholder.com/300x200?text=Cow',
            farmer=farmer
        ),
        Animal(
            name='Billy the Goat',
            animal_type=AnimalType.GOAT,
            breed='Boer',
            age=12,
            price=300.00,
            weight=45.00,
            description='Strong Boer goat, excellent for meat production.',
            image_url='https://via.placeholder.com/300x200?text=Goat',
            farmer=farmer
        ),
        Animal(
            name='Chicken Flock',
            animal_type=AnimalType.POULTRY,
            breed='Rhode Island Red',
            age=6,
            price=25.00,
            weight=2.50,
            description='Healthy laying hens, great for egg production.',
            image_url='https://via.placeholder.com/300x200?text=Chicken',
            farmer=farmer
        )
    ]
    
    try:
        db.session.add(farmer)
        db.session.add(user)
        for animal in animals:
            db.session.add(animal)
        db.session.commit()
        print("Database initialized successfully!")
        print("Sample farmer: farmer@example.com / password123")
        print("Sample user: user@example.com / password123")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing database: {e}")