from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import CartItem, Animal, User

cart_bp = Blueprint('cart', __name__)
