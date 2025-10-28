from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import enum

# Import the db instance from the app package
from app import db, bcrypt


class UserType(enum.Enum):
    FARMER = "farmer"
    USER = "user"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    animals = db.relationship(
        "Animal",
        backref="farmer",
        lazy=True,
        cascade="all, delete-orphan",
        foreign_keys="Animal.farmer_id",
    )
    orders = db.relationship(
        "Order", backref="user", lazy=True, foreign_keys="Order.user_id"
    )
    cart_items = db.relationship(
        "CartItem", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "user_type": self.user_type.value,
            "phone": self.phone,
            "address": self.address,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AnimalType(enum.Enum):
    CATTLE = "cattle"
    POULTRY = "poultry"
    SWINE = "swine"
    SHEEP = "sheep"
    GOAT = "goat"


class Animal(db.Model):
    __tablename__ = "animals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    animal_type = db.Column(db.Enum(AnimalType), nullable=False, index=True)
    breed = db.Column(db.String(100), nullable=False, index=True)
    age = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    is_available = db.Column(db.Boolean, default=True, index=True)
    farmer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "animal_type": self.animal_type.value,
            "breed": self.breed,
            "age": self.age,
            "price": self.price,
            "weight": self.weight,
            "description": self.description,
            "image_url": self.image_url,
            "is_available": self.is_available,
            "farmer": {
                "id": self.farmer.id,
                "first_name": self.farmer.first_name,
                "last_name": self.farmer.last_name,
                "email": self.farmer.email,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    COMPLETED = "completed"


# FIXED: Single Order class definition with all fields
class Order(db.Model):
    __tablename__ = "orders"
    __table_args__ = {"extend_existing": True}  # Prevents table redefinition errors

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    payment_intent_id = db.Column(db.String(100))  # M-Pesa CheckoutRequestID
    payment_status = db.Column(
        db.String(20), default="pending"
    )  # pending, completed, failed
    shipping_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    order_items = db.relationship(
        "OrderItem", backref="order", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "total_amount": self.total_amount,
            "status": self.status.value,
            "payment_status": self.payment_status,
            "payment_intent_id": self.payment_intent_id,
            "shipping_address": self.shipping_address,
            "notes": self.notes,
            "user": self.user.to_dict(),
            "order_items": [item.to_dict() for item in self.order_items],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"
    __table_args__ = {"extend_existing": True}  # Prevents table redefinition errors

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True
    )
    animal_id = db.Column(db.Integer, db.ForeignKey("animals.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)

    animal = db.relationship("Animal", backref="order_items")

    def to_dict(self):
        return {
            "id": self.id,
            "animal": self.animal.to_dict(),
            "quantity": self.quantity,
            "price": self.price,
            "subtotal": self.price * self.quantity,
        }


class CartItem(db.Model):
    __tablename__ = "cart_items"
    __table_args__ = {"extend_existing": True}  # Prevents table redefinition errors

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    animal_id = db.Column(db.Integer, db.ForeignKey("animals.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    animal = db.relationship("Animal", backref="cart_items")

    def to_dict(self):
        return {
            "id": self.id,
            "animal": self.animal.to_dict(),
            "quantity": self.quantity,
            "added_at": self.added_at.isoformat(),
            "subtotal": self.animal.price * self.quantity,
        }
