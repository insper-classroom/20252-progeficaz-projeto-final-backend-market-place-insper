from datetime import datetime
from mongoengine import (
    Document, StringField, EmailField, DateTimeField,
    ReferenceField, FloatField, BooleanField, NULLIFY, CASCADE
)
from werkzeug.security import generate_password_hash, check_password_hash

class User(Document):
    meta = {
        "collection": "users",
        "indexes": ["email"]
    }
    email = EmailField(required=True, unique=True)
    name = StringField(required=True, max_length=120)
    password_hash = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": str(self.id), "email": self.email, "name": self.name, "created_at": self.created_at.isoformat()}

class Cellphone(Document):
    meta = {"collection": "cellphones"}
    number = StringField(required=True, unique=True)
    model = StringField()
    user = ReferenceField(User, reverse_delete_rule=NULLIFY)
    created_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "number": self.number,
            "model": self.model,
            "user_id": str(self.user.id) if self.user else None,
            "created_at": self.created_at.isoformat()
        }

class Product(Document):
    meta = {
        "collection": "products",
        "indexes": ["owner", "buyer", "confirmation_code"]
    }
    title = StringField(required=True, max_length=200)
    description = StringField()
    price = FloatField(required=True, min_value=0.0)
    owner = ReferenceField(User, required=True, reverse_delete_rule=CASCADE)   # proprietário (obrigatório)
    buyer = ReferenceField(User, required=False, null=True, reverse_delete_rule=NULLIFY)  # comprador (null até confirmar com código)
    confirmation_code = StringField(unique=True, sparse=True)  # código gerado pelo owner (se existe, owner confirmou)
    created_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "owner_id": str(self.owner.id) if self.owner else None,
            "buyer_id": str(self.buyer.id) if self.buyer else None,
            "created_at": self.created_at.isoformat()
        }
