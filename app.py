
from flask import Flask, redirect, url_for, request, jsonify, current_app, Blueprint
from flask_cors import CORS
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

#  ============================ APP SETUP ============================
def create_app():
    app = Flask(__name__)
    connect_db(app)
    print('Banco de dados conectado com sucesso!')

# CORS = faz conexoes externas
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:5173", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    
# registrando blueprint
    from routes.items import items_blueprint
    from routes.auth import auth_blueprint
    app.register_blueprint(items_blueprint, url_prefix="")
    app.register_blueprint(auth_blueprint, url_prefix="") # registra as rotas do items e auth _blueprint no app principal
    return app

    app.config.from_object("config.Config")
    connect_db(app)
    app.register_blueprint(items_blueprint, url_prefix="/")

    # verificar disponibilidade de redes
    @app.route("/ping")
    def ping():
        return jsonify({"ok": True, "mensagem": "Conexão Flask funcionando!"})

    # rota que retorna dados para a página
    @app.route("/home")
    def home_api():
        return jsonify({
            "titulo": "Página Home (vinda do Flask)",
            "mensagem": "Backend conectado!"
        })
        
    @app.route('/')
    def home():
        return jsonify({
            "status": "online",
            "message": "API Marketplace Insper"
        })


    # fechamento de conexões quando o app encerrar
    @app.teardown_appcontext
    def close_db(exception):
        client = getattr(app, "mongo_client", None)
        if client:
            client.close()

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

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "condition": self.condition,
            "photos": self.photos,
            "category": self.category,
            "seller_id": self.seller_id,
            "status": self.status,
            "boosted": self.boosted,
            "created_at": self.created_at
        }


# ============================ DATABASE SETUP ============================
# guardando as variáveis do banco de dados
load_dotenv('.cred')
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_USERS = os.getenv("COLLECTION_USERS")
COLLECTION_ITEMS = os.getenv("COLLECTION_ITEMS")


def connect_db(app):
    try:
        # tenta conectar o cliente e banco de dados ao app
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        app.mongo_client = client
        if DB_NAME:
            app.db = client[DB_NAME]
            print(f'Conectado ao banco de dados: {DB_NAME}')
        else:
            client.get_database(DB_NAME)
    except Exception as e:
        raise RuntimeError(f"Erro ao conectar ao banco de dados: {e}")

def get_db(): 
    print(f'Acessando banco de dados: {current_app.db.name}')
    return current_app.db # retorna o banco de dados atrelado ao app


# ============================ RUN APP ============================

if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
