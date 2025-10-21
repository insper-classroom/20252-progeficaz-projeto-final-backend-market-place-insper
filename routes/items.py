from flask import Blueprint, request, jsonify, current_app
from bson.objectid import ObjectId # serve para identificar documentos no MongoDB
import os

items_blueprint = Blueprint("items", __name__)
'''
BLUEPRINT
-> É um componente reutilizável que junta rotas, modelos etc.

Como funciona:
1. criar a blueprint
2. registrar ela no app
3. definir rotas

Definindo as rotas: 
@items_blueprint.route("/", methods=["GET"]) => rota para o método GET e terminação "/"
'''

def get_collection(name): # pega a coleção do banco de dados atrelado ao app pelo nome
    print(f'Acessando coleção: {name}')
    return current_app.db[name] 


@items_blueprint.route("/", methods=["GET"])
def get_items():
    print(f'Método da request: {request.method}')
    try:
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS")) # lista todos os docs da coleção
        items = list(items_collection.find({})) # converte o cursor em lista
        for e in items:    
            e["_id"] = str(e["_id"]) # Converte ObjectId em string
        return jsonify(items), 200
    except Exception as e:
        print(f"Erro ao listar itens: {e}")
        return jsonify({"error": "Erro ao listar itens"}), 500


# @items_blueprint.route("/", methods=["POST"])
# def create_item():
#     data = request.get_json(silent=True) or {}
#     item = {"name": data.get("name"), "description": data.get("description")}
#     res = items_collection().insert_one(item)
#     item["_id"] = str(res.inserted_id)
#     return jsonify(item), 201

# @items_blueprint.route("/<id>", methods=["GET"])
# def get_item(id):
#     try:
#         doc = items_collection().find_one({"_id": ObjectId(id)})
#     except:
#         return jsonify({"error": "id inválido"}), 400
#     if not doc:
#         return jsonify({"error": "não encontrado"}), 404
#     doc["_id"] = str(doc["_id"])
#     return jsonify(doc), 200

# @items_blueprint.route("/<id>", methods=["PUT"])
# def update_item(id):
#     try:
#         oid = ObjectId(id)
#     except:
#         return jsonify({"error": "id inválido"}), 400
#     data = request.get_json(silent=True) or {}
#     update = {"$set": {"name": data.get("name"), "description": data.get("description")}}
#     res = items_collection().update_one({"_id": oid}, update)
#     if res.matched_count == 0:
#         return jsonify({"error": "não encontrado"}), 404
#     doc = items_collection().find_one({"_id": oid})
#     doc["_id"] = str(doc["_id"])
#     return jsonify(doc), 200

# @items_blueprint.route("/<id>", methods=["DELETE"])
# def delete_item(id):
#     try:
#         oid = ObjectId(id)
#     except:
#         return jsonify({"error": "id inválido"}), 400
#     res = items_collection().delete_one({"_id": oid})
#     if res.deleted_count == 0:
#         return jsonify({"error": "não encontrado"}), 404
#     return jsonify({"deleted": id}), 200
