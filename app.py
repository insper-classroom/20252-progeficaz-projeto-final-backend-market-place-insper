from flask import Flask, redirect, url_for, request, jsonify, Blueprint
from flask_cors import CORS
from routes.items import items_bp
from models.db import init_db
from datetime import datetime


def create_app():
    app = Flask(__name__)

# CORS = faz conexoes externas
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })


    app.config.from_object("config.Config")
    init_db(app)
    app.register_blueprint(items_bp, url_prefix="/api/items")

    # verificar disponibilidade de redes
    @app.route("/api/ping")
    def ping():
        return jsonify({"ok": True, "mensagem": "Conexão Flask OK"})

    # Rota que retorna dados para a página Home (exemplo)
    @app.route("/api/home")
    def home_api():
        return jsonify({
            "titulo": "Página Home (vinda do Flask)",
            "mensagem": "Seja bem-vindo ao backend conectado!"
        })

    # Garante fechamento de conexões quando o app encerrar contexto
    @app.teardown_appcontext
    def close_db(exception):
        client = getattr(app, "mongo_client", None)
        if client:
            client.close()

    @app.route('/')
    def home():
        if request.method == 'POST':
            return jsonify({"redirect_url": url_for("login", _external=True)})
        return jsonify({"redirect_url": url_for("home", _external=True)})

    return app


class Product:
    def __init__(self, id, title, description, price, condition, photos, category_id, seller_id, status):
        self.id = id
        self.title = title
        self.description = description
        self.price = price
        self.condition = condition
        self.photos = photos 
        self.category_id = category_id
        self.seller_id = seller_id
        self.status = status
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "condition": self.condition,
            "photos": self.photos,
            "category_id": self.category_id,
            "seller_id": self.seller_id,
            "status": self.status,
            "created_at": self.created_at
        }


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
