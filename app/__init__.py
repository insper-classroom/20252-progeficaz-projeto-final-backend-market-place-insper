from flask import Flask
from flask_cors import CORS
from .extensions import init_db, init_jwt, init_cloudinary
from .routes.auth import bp as auth_bp
from .routes.products import bp as products_bp
import os
from dotenv import load_dotenv

def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=False)

    # setup do CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # acessando .env 
    load_dotenv()

    # carregando variaveis do env 
    for k, v in os.environ.items():
        if k.isupper():
            app.config[k] = v

    init_db(app)
    init_jwt(app)
    init_cloudinary(app)

    # registrando blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)

    return app
