from mongoengine import connect, get_db
from flask_jwt_extended import JWTManager

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
