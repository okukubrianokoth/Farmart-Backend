from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Animal, AnimalType, User, UserType
from sqlalchemy import or_

animals_bp = Blueprint('animals', __name__)

@animals_bp.route('/animals', methods=['GET'])
def get_animals():
    animal_type = request.args.get('type')
    breed = request.args.get('breed')
    min_age = request.args.get('min_age')
    max_age = request.args.get('max_age')

    query = Animal.query.filter_by(is_available=True)
    
    if animal_type:
        query = query.filter_by(animal_type=AnimalType(animal_type))
    if breed:
        query = query.filter(Animal.breed.ilike(f'%{breed}%'))
    if min_age:
        query = query.filter(Animal.age >= int(min_age))
    if max_age:
        query = query.filter(Animal.age <= int(max_age))
    
    animals = query.all()

    return jsonify([{
        'id': animal.id,
        'name': animal.name,
        'animal_type': animal.animal_type.value,
        'breed': animal.breed,
        'age': animal.age,
        'price': animal.price,
        'weight': animal.weight,
        'description': animal.description,
        'image_url': animal.image_url,
        'is_available': animal.is_available,
        'farmer': {
            'id': animal.farmer.id,
            'first_name': animal.farmer.first_name,
            'last_name': animal.farmer.last_name
        }
    } for animal in animals])

@animals_bp.route('/animals', methods=['POST'])
@jwt_required()
def create_animal():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        
        if user.user_type != UserType.FARMER:
            return jsonify({'message': 'Only farmers can add animals'}), 403
        
        data = request.get_json()
        
        if not data or not all(k in data for k in ['name', 'animal_type', 'breed', 'age', 'price']):
            return jsonify({'message': 'Missing required fields'}), 400
        
        # Ensure new animals are available by default
        animal = Animal(
            name=data['name'],
            animal_type=AnimalType(data['animal_type']),
            breed=data['breed'],
            age=data['age'],
            price=data['price'],
            weight=data.get('weight'),
            description=data.get('description'),
            image_url=data.get('image_url'),
            farmer_id=current_user_id,
            is_available=True  # This ensures new animals are available
        )

        db.session.add(animal)
        db.session.commit()

         return jsonify({
            'message': 'Animal added successfully',
            'animal': animal.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to add animal', 'error': str(e)}), 500
    
@animals_bp.route('/animals/<int:animal_id>', methods=['PUT'])   
@jwt_required()
def update_animal(animal_id):
    current_user_id = get_jwt_identity()
    animal = Animal.query.get_or_404(animal_id)
    
    if animal.farmer_id != current_user_id:
        return jsonify({'message': 'Not authorized'}), 403
    
        