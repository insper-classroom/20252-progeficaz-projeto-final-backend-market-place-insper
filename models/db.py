from pymongo import MongoClient
from flask import current_app

def init_db(app):
    uri = app.config.get("MONGO_URI")
    client = MongoClient(uri)
    app.mongo_client = client
    app.db = client.get_database()

def get_db():
    return current_app.db
