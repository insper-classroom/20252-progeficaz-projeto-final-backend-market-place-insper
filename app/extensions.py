from mongoengine import connect, get_db
from flask_jwt_extended import JWTManager
import cloudinary

_db = None
_jwt = None

def init_db(app):
    """
    Inicializa a conexão mongoengine e guarda a instancia do pymongo Database.
    """
    global _db
    connect(host=app.config["MONGO_URI"], alias="default")
    _db = get_db()  # retorna objeto pymongo.database.Database

def get_pymongo_db():
    if _db is None:
        raise RuntimeError("DB não inicializado. Chame init_db(app) primeiro.")
    return _db

def init_jwt(app):
    global _jwt
    _jwt = JWTManager(app)

def init_cloudinary(app):
    """
    Inicializa configuração do Cloudinary.
    """
    cloudinary.config(
        cloud_name=app.config.get("CLOUDINARY_CLOUD_NAME"),
        api_key=app.config.get("CLOUDINARY_API_KEY"),
        api_secret=app.config.get("CLOUDINARY_API_SECRET"),
        secure=True
    )
