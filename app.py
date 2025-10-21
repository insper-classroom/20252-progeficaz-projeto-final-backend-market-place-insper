from flask import Flask, current_app, request
from pymongo import MongoClient
import os
from flask import jsonify
from dotenv import load_dotenv

# variáveis do banco de dados
load_dotenv('.cred')
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_USERS = os.getenv("COLLECTION_USERS")
COLLECTION_ITEMS = os.getenv("COLLECTION_ITEMS")

# ============================ DATABASE SETUP ============================
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


# ============================ APP SETUP ============================
def create_app():
    app = Flask(__name__)    
    connect_db(app)
    print('Banco de dados conectado com sucesso!')
    
# registrando blueprint
    from routes.items import items_blueprint
    app.register_blueprint(items_blueprint, url_prefix="") # registra as rotas do items_blueprint no app principal
    return app

# @app.teardown_appcontext
# def close_db(exception):
#     client = getattr(app, "mongo_client", None)
#     # if client:
#     #     client.close()


# ============================ RUN APP ============================
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
