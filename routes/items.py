from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from models.db import get_db

items_bp = Blueprint("items", __name__)

def _col():
    return get_db()["items"]

@items_bp.route("/", methods=["GET"])
def list_items():
    docs = list(_col().find({}))
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify(docs), 200

@items_bp.route("/", methods=["POST"])
def create_item():
    data = request.get_json(silent=True) or {}
    item = {"name": data.get("name"), "description": data.get("description")}
    res = _col().insert_one(item)
    item["_id"] = str(res.inserted_id)
    return jsonify(item), 201

@items_bp.route("/<id>", methods=["GET"])
def get_item(id):
    try:
        doc = _col().find_one({"_id": ObjectId(id)})
    except:
        return jsonify({"error": "id inválido"}), 400
    if not doc:
        return jsonify({"error": "não encontrado"}), 404
    doc["_id"] = str(doc["_id"])
    return jsonify(doc), 200

@items_bp.route("/<id>", methods=["PUT"])
def update_item(id):
    try:
        oid = ObjectId(id)
    except:
        return jsonify({"error": "id inválido"}), 400
    data = request.get_json(silent=True) or {}
    update = {"$set": {"name": data.get("name"), "description": data.get("description")}}
    res = _col().update_one({"_id": oid}, update)
    if res.matched_count == 0:
        return jsonify({"error": "não encontrado"}), 404
    doc = _col().find_one({"_id": oid})
    doc["_id"] = str(doc["_id"])
    return jsonify(doc), 200

@items_bp.route("/<id>", methods=["DELETE"])
def delete_item(id):
    try:
        oid = ObjectId(id)
    except:
        return jsonify({"error": "id inválido"}), 400
    res = _col().delete_one({"_id": oid})
    if res.deleted_count == 0:
        return jsonify({"error": "não encontrado"}), 404
    return jsonify({"deleted": id}), 200
