from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import CartItem, Order, OrderItem, OrderStatus, Animal, User, UserType

orders_bp = Blueprint("orders", __name__)


# FIXED: Changed from '/user/my-orders' to '/orders/user/my-orders' to match frontend call
@orders_bp.route("/orders/user/my-orders", methods=["GET"])
@jwt_required()
def get_user_orders():
    """Get all orders for the current user"""
    current_user_id = get_jwt_identity()

    try:
        # Get user's orders with their items and animal details
        orders = (
            Order.query.filter_by(user_id=current_user_id)
            .order_by(Order.created_at.desc())
            .all()
        )

        orders_data = []
        for order in orders:
            order_data = {
                "id": order.id,
                "total_amount": order.total_amount,
                "status": order.status.value,
                "created_at": order.created_at.isoformat(),
                "order_items": [],
            }

            # Add order items with animal details
            for item in order.order_items:
                subtotal = item.quantity * item.price

                order_data["order_items"].append(
                    {
                        "id": item.id,
                        "animal": {
                            "name": item.animal.name,
                            "breed": item.animal.breed,
                        },
                        "quantity": item.quantity,
                        "price": item.price,
                        "subtotal": subtotal,
                    }
                )

            orders_data.append(order_data)

        return jsonify({"orders": orders_data})

    except Exception as e:
        return jsonify({"message": "Error fetching orders", "error": str(e)}), 500


# FIXED: Changed from '/farmer/my-sales' to '/orders/farmer/my-sales' to match frontend call
@orders_bp.route("/orders/farmer/my-sales", methods=["GET"])
@jwt_required()
def get_farmer_orders():
    """Get orders for farmer's animals - matches frontend endpoint"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user.user_type != UserType.FARMER:
        return jsonify({"message": "Only farmers can view these orders"}), 403

    try:
        # Get orders containing animals from this farmer
        orders = (
            Order.query.join(OrderItem)
            .join(Animal)
            .filter(Animal.farmer_id == current_user_id)
            .distinct()
            .all()
        )

        orders_data = []
        for order in orders:
            order_data = {
                "id": order.id,
                "total_amount": order.total_amount,
                "status": order.status.value,
                "created_at": order.created_at.isoformat(),
                "user": {
                    "first_name": order.user.first_name,
                    "last_name": order.user.last_name,
                    "email": order.user.email,
                },
                "order_items": [],
            }

            # Only include items from this farmer
            for item in order.order_items:
                if item.animal.farmer_id == current_user_id:
                    subtotal = item.quantity * item.price
                    order_data["order_items"].append(
                        {
                            "animal_name": item.animal.name,
                            "quantity": item.quantity,
                            "price": item.price,
                            "subtotal": subtotal,
                        }
                    )

            orders_data.append(order_data)

        return jsonify({"orders": orders_data})

    except Exception as e:
        return (
            jsonify({"message": "Error fetching farmer orders", "error": str(e)}),
            500,
        )


# FIXED: Changed from '/checkout' to '/orders/checkout' to match frontend call
@orders_bp.route("/orders/checkout", methods=["POST"])
@jwt_required()
def checkout():
    """Checkout cart and create order"""
    try:
        current_user_id = get_jwt_identity()
        print(f"🛒 Checkout started for user {current_user_id}")

        # Get user's cart items
        cart_items = CartItem.query.filter_by(user_id=current_user_id).all()
        print(f"📦 Found {len(cart_items)} cart items")

        if not cart_items:
            return jsonify({"message": "Cart is empty"}), 400

        # Calculate total
        total_amount = sum(item.animal.price * item.quantity for item in cart_items)
        print(f"💰 Total amount: ${total_amount}")

        # Get shipping address from request
        data = request.get_json() or {}
        shipping_address = data.get("shipping_address", "Default address")

        # Create order
        order = Order(
            user_id=current_user_id,
            total_amount=total_amount,
            shipping_address=shipping_address,
            notes=data.get("notes", ""),
        )
        db.session.add(order)
        db.session.flush()  # Get order ID without committing

        print(f"📝 Created order #{order.id}")

        # Create order items and mark animals as unavailable
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                animal_id=cart_item.animal_id,
                quantity=cart_item.quantity,
                price=cart_item.animal.price,
            )
            db.session.add(order_item)

            # Mark animal as unavailable
            cart_item.animal.is_available = False
            print(f"🐮 Marked animal {cart_item.animal_id} as unavailable")

        # Clear cart
        deleted_count = CartItem.query.filter_by(user_id=current_user_id).delete()
        print(f"🗑️ Cleared {deleted_count} cart items")

        db.session.commit()

        print("✅ Checkout completed successfully")

        return (
            jsonify(
                {
                    "message": "Order placed successfully",
                    "order_id": order.id,
                    "total_amount": total_amount,
                    "order": order.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"❌ Checkout error: {str(e)}")
        return jsonify({"message": "Checkout failed", "error": str(e)}), 500


# FIXED: Changed from '/<int:order_id>/status' to '/orders/<int:order_id>/status' for consistency
@orders_bp.route("/orders/<int:order_id>/status", methods=["PUT"])
@jwt_required()
def update_order_status(order_id):
    current_user_id = get_jwt_identity()
    order = Order.query.get_or_404(order_id)

    # Check if current user is farmer for any animal in this order
    is_farmer = any(
        item.animal.farmer_id == current_user_id for item in order.order_items
    )

    if not is_farmer:
        return jsonify({"message": "Not authorized"}), 403

    data = request.get_json()
    order.status = OrderStatus(data["status"])
    db.session.commit()

    return jsonify({"message": "Order status updated"})
