from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Animal, AnimalType, User, UserType
from sqlalchemy import or_

animals_bp = Blueprint('animals', __name__)