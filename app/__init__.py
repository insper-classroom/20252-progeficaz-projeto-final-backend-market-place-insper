from flask import Flask
from flask_cors import CORS
from .extensions import init_db, init_jwt, init_cloudinary
from .routes.auth import bp as auth_bp
from .routes.products import bp as products_bp
import os
from dotenv import load_dotenv

def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=False)

    # Enable CORS for all routes and origins
    CORS(app, resources={r"/*": {"origins": "*"}})

    # load .env into environment
    load_dotenv()

    # copy env vars into app.config
    for k, v in os.environ.items():
        if k.isupper():
            app.config[k] = v

    init_db(app)
    init_jwt(app)
    init_cloudinary(app)

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)

    return app
