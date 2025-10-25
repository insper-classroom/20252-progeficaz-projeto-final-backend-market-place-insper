from flask import Flask, redirect, url_for, request, jsonify, current_app, Blueprint
from flask_cors import CORS
from datetime import datetime
from pymongo import MongoClient, errors
import os
from dotenv import load_dotenv
from utils import init_app
from bson import ObjectId

# ============================ DATABASE SETUP ============================
load_dotenv('.cred')
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_USERS = os.getenv("COLLECTION_USERS")
COLLECTION_ITEMS = os.getenv("COLLECTION_ITEMS")


def connect_db(app):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # checa conexão
        client.admin.command("ping")

        app.mongo_client = client
        if DB_NAME:
            app.db = client[DB_NAME]
            print(f'Conectado ao banco de dados: {DB_NAME}')
        else:
            client.get_database(DB_NAME)

        validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["title", "description", "price", "category", "seller_id", "status", "created_at"],
                "properties": {
                    "_id": {"bsonType": ["objectId", "string"]},
                    "title": {"bsonType": "string"},
                    "description": {"bsonType": "string"},
                    "price": {"bsonType": ["double", "int", "decimal"], "minimum": 0},
                    "condition": {"bsonType": "string", "enum": ["Novo", "Usado", "Seminovo"]},
                    "images": {"bsonType": "array", "items": {"bsonType": "string"}},  # ← ADICIONADO
                    "category": {"bsonType": "string"},
                    "seller_id": {"bsonType": ["objectId", "string"]},
                    "status": {"bsonType": "string", "enum": ["Rascunho", "Ativo", "Vendido", "Removido"]},
                    "boosted": {"bsonType": "bool"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}},
                "additionalProperties": True}
            }

        db = app.db # cria coleção com validator ou att
        colecao = COLLECTION_ITEMS
        try:
            if colecao in db.list_collection_names():
                # att
                result = db.command({
                    "collMod": colecao,
                    "validator": validator,
                    "validationLevel": "moderate",
                    "validationAction": "error"
                })
                print(f"Validator atualizado para a coleção: '{colecao}'.")
                print(f"Resultado: {result}")
            else: # cria coleção com validator 
                db.create_collection(
                    colecao,
                    validator=validator,
                    validationLevel="moderate",
                    validationAction="error")
                print(f"Coleção '{colecao}' criada com validator.")
        except errors.OperationFailure as e:
            print(f"Erro ao aplicar validator: {e}")
          
    except Exception as e:
        raise RuntimeError(f"Erro ao conectar ao banco de dados: {e}")
    
    
def get_db():
    print(f'Acessando banco de dados: {current_app.db.name}')
    return current_app.db


#  ============================ APP SETUP ============================
def create_app():
    app = Flask(__name__)
    connect_db(app)
    app = init_app(app)  # inicializa JWT e Bcrypt
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    print('Banco de dados conectado com sucesso!')

    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:5173", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    from routes.items import items_blueprint
    from routes.auth import auth_blueprint
    app.register_blueprint(items_blueprint, url_prefix="")
    app.register_blueprint(auth_blueprint, url_prefix="")
    return app


# ============================ CLASSES ============================
class Product:
    def __init__(self, id, title, description, price, condition, photos, category, seller_id, status, boosted):
        self.id = id
        self.title = title
        self.description = description
        self.price = price
        self.condition = condition
        self.photos = photos
        self.category = category
        self.seller_id = seller_id
        self.status = status
        self.boosted = boosted
        self.created_at = datetime.now()
        self.updated_at = None

    def to_document(self):
        """
        Mapeia a instância para o documento MongoDB.
        Se `id` for um ObjectId válido, usa como ObjectId, senão guarda como string.
        Retorna dicionário pronto pra insert/update.
        """
        # id -> _id
        _id = None
        if self.id:
            try:
                _id = ObjectId(str(self.id)) if ObjectId.is_valid(str(self.id)) else str(self.id)
            except Exception:
                _id = str(self.id)

        # seller_id 
        seller = None
        if self.seller_id:
            try:
                seller = ObjectId(str(self.seller_id)) if ObjectId.is_valid(str(self.seller_id)) else str(self.seller_id)
            except Exception:
                seller = str(self.seller_id)

        item = {
            **({"_id": _id} if _id is not None else {}),
            "title": self.title,
            "description": self.description,
            "price": float(self.price) if self.price is not None else None,
            "condition": self.condition,
            "photos": self.photos or [],
            "category": self.category,
            "seller_id": seller,
            "status": self.status,
            "boosted": bool(self.boosted),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        return item


# ============================ RUN APP ============================
if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
