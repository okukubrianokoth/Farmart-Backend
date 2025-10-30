from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import CartItem, Animal, User

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    try:
        current_user_id = get_jwt_identity()
        cart_items = CartItem.query.filter_by(user_id=current_user_id).all()
        
        total = sum(item.animal.price * item.quantity for item in cart_items)
        item_count = len(cart_items)
        
        return jsonify({
            'items': [{
                'id': item.id,
                'animal': {
                    'id': item.animal.id,
                    'name': item.animal.name,
                    'animal_type': item.animal.animal_type.value,
                    'breed': item.animal.breed,
                    'age': item.animal.age,
                    'price': item.animal.price,
                    'weight': item.animal.weight,
                    'description': item.animal.description,
                    'image_url': item.animal.image_url,
                    'is_available': item.animal.is_available,
                    'farmer': {
                        'id': item.animal.farmer.id,
                        'first_name': item.animal.farmer.first_name,
                        'last_name': item.animal.farmer.last_name
                    }
                },
                'quantity': item.quantity,
                'added_at': item.added_at.isoformat() if item.added_at else None
            } for item in cart_items],
            'total': total,
            'item_count': item_count
        })
    
    except Exception as e:
        return jsonify({'message': 'Failed to fetch cart', 'error': str(e)}), 500

