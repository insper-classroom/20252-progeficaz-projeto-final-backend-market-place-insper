from flask import Flask
from routes.items import items_bp
from models.db import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    init_db(app)
    app.register_blueprint(items_bp, url_prefix="/api/items")

    @app.teardown_appcontext
    def close_db(exception):
        client = getattr(app, "mongo_client", None)
        if client:
            client.close()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
