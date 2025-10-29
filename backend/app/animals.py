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