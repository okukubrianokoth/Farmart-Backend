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