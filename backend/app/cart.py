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
    

@cart_bp.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'animal_id' not in data:
            return jsonify({'message': 'Animal ID is required'}), 400
        
        animal = Animal.query.get_or_404(data['animal_id'])
        
        if not animal.is_available:
            return jsonify({'message': 'Animal is not available for purchase'}), 400
        
        # Check if user is trying to buy their own animal
        if animal.farmer_id == current_user_id:
            return jsonify({'message': 'You cannot buy your own animal'}), 400
        
        quantity = data.get('quantity', 1)
        
        if quantity < 1:
            return jsonify({'message': 'Quantity must be at least 1'}), 400
        
        # Check if item already in cart
        cart_item = CartItem.query.filter_by(
            user_id=current_user_id, 
            animal_id=data['animal_id']
        ).first()
        
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                user_id=current_user_id,
                animal_id=data['animal_id'],
                quantity=quantity
            )
            db.session.add(cart_item)
        
        db.session.commit()

        return jsonify({
            'message': 'Added to cart successfully',
            'cart_item': {
                'id': cart_item.id,
                'animal_id': cart_item.animal_id,
                'quantity': cart_item.quantity,
                'added_at': cart_item.added_at.isoformat() if cart_item.added_at else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to add to cart', 'error': str(e)}), 500
    

@cart_bp.route('/cart/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(item_id):
    try:
        current_user_id = get_jwt_identity()
        cart_item = CartItem.query.filter_by(id=item_id, user_id=current_user_id).first_or_404()
        
        data = request.get_json()
        quantity = data.get('quantity')
        
        if quantity is None:
            return jsonify({'message': 'Quantity is required'}), 400
        
        if quantity < 1:
            return jsonify({'message': 'Quantity must be at least 1'}), 400
        
        if not cart_item.animal.is_available:
            return jsonify({'message': 'Animal is no longer available'}), 400
        
        cart_item.quantity = quantity
        db.session.commit()

        return jsonify({
            'message': 'Cart updated successfully',
            'cart_item': {
                'id': cart_item.id,
                'quantity': cart_item.quantity
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update cart', 'error': str(e)}), 500

@cart_bp.route('/cart/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    try:
        current_user_id = get_jwt_identity()
        cart_item = CartItem.query.filter_by(id=item_id, user_id=current_user_id).first_or_404()

        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'message': 'Item removed from cart'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to remove from cart', 'error': str(e)}), 500

