from flask import Flask, redirect, url_for, request, jsonify
from flask_cors import CORS
from routes.items import items_bp
from models.db import init_db

app = Flask(__name__)
CORS(app)
def create_app():
    app.config.from_object("config.Config")
    init_db(app)
    app.register_blueprint(items_bp, url_prefix="/api/items")

    @app.teardown_appcontext
    def close_db(exception):
        client = getattr(app, "mongo_client", None)
        if client:
            client.close()

    return app

@app.route('/')
def home():
    if request.method == 'POST':
        return jsonify({"redirect_url": url_for("login", _external=True)})
    return jsonify({"redirect_url": url_for("home", _external=True)})

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
