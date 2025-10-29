from datetime import datetime
from mongoengine import (
    Document, StringField, EmailField, DateTimeField,
    ReferenceField, FloatField, BooleanField, ListField, NULLIFY, CASCADE
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
    cellphone = StringField(required=True)
    favorites = ListField(ReferenceField('Product'), default=list)
    created_at = DateTimeField(default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": str(self.id), "email": self.email, "name": self.name, "cellphone": self.cellphone, "created_at": self.created_at.isoformat()}

class Product(Document):
    meta = {
        "collection": "products",
        "indexes": ["owner", "buyer", "confirmation_code", "category", "em_destaque"]
    }
    title = StringField(required=True, max_length=200)
    description = StringField()
    price = FloatField(required=True, min_value=0.0)
    category = StringField(required=True, choices=["eletrodomésticos", "eletrônicos", "móveis", "outros"])
    estado_de_conservacao = StringField(required=True, choices=["novo", "seminovo", "usado"])
    em_destaque = BooleanField(default=False)  # campo para anúncios pagos em destaque
    owner = ReferenceField(User, required=True, reverse_delete_rule=CASCADE)   # proprietário (obrigatório)
    buyer = ReferenceField(User, required=False, null=True, reverse_delete_rule=NULLIFY)  # comprador (null até confirmar com código)
    confirmation_code = StringField(unique=True, sparse=True)  # código gerado pelo owner (se existe, owner confirmou)
    images = ListField(StringField(), default=list)  # lista de URLs das imagens no Cloudinary
    created_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "category": self.category,
            "estado_de_conservacao": self.estado_de_conservacao,
            "em_destaque": self.em_destaque,
            "owner": self.owner.to_dict() if self.owner else None,
            "buyer": self.buyer.to_dict() if self.buyer else None,
            "images": self.images,
            "thumbnail": self.images[0] if self.images else None,
            "created_at": self.created_at.isoformat()
        }
