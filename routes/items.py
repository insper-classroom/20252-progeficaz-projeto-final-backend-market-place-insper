from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
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


def token_required_import(): # importa o decorador token_required 
    from routes.auth import token_required
    return token_required

# ============================ ROTAS ============================
# * ========================================== GET ========================================== *
@items_blueprint.route("/items", methods=["GET"])
def get_items():
    """Lista todos os itens"""
    print(f'Método: {request.method}')
    try:
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS")) # lista todos os docs da coleção
        items = list(items_collection.find({})) # converte o cursor em lista
        for item in items:    
            item["_id"] = str(item["_id"]) # converte ObjectId em string
        return jsonify(items), 200
    except Exception as e:
        print(f"Erro ao listar itens: {e}")
        return jsonify({"error": "Erro ao listar itens"}), 500 # erro interno do servidor


@items_blueprint.route("/items/<id>", methods=["GET"])
def get_item(id):
    """Busca item por ID"""
    try:
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        doc = items_collection.find_one({"_id": ObjectId(id)})
        if not doc:
            return jsonify({"error": "Product not found"}), 404
        doc["_id"] = str(doc["_id"])
        return jsonify(doc), 200
    except Exception as e:
        print(f"Erro ao buscar item: {e}")
        return jsonify({"error": "ID inválido"}), 400 # bad request 
    

@items_blueprint.route("/items/category/<category>", methods=["GET"])
def get_items_by_category(category):
    """Lista itens por categoria"""
    try:
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        items = list(items_collection.find({"category": category}))
        for item in items:
            item["_id"] = str(item["_id"])
        return jsonify(items), 200
    except Exception as e:
        print(f"Erro ao buscar por categoria: {e}")
        return jsonify({"error": "Erro ao buscar itens"}), 500


@items_blueprint.route("/items/seller/<seller_id>", methods=["GET"])
def get_items_by_seller(seller_id):
    """Lista itens por vendedor"""
    try:
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        items = list(items_collection.find({"seller_id": seller_id}))
        for item in items:
            item["_id"] = str(item["_id"])
        return jsonify(items), 200
    except Exception as e:
        print(f"Erro ao buscar por vendedor: {e}")
        return jsonify({"error": "Erro ao buscar itens"}), 500


# * ========================================== POST ========================================== *
@items_blueprint.route("/items", methods=["POST"])
def create_item():
    """Cria novo item"""
    token_required = token_required_import()

    @token_required
    def _create(current_user):
        try:
            data = request.get_json()
            
            if not data or not data.get("title") or data.get("price", -1) <= 0: # validação básica
                return jsonify({"error": "Dados inválidos"}), 400
            
            data["seller_id"] = current_user["_id"] # adds seller_id automaticamente do user autenticado
            data["created_at"] = datetime.now()
            data["status"] = data.get("status", "Ativo")
            
            items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
            result = items_collection.insert_one(data)
            
            return jsonify({
                "message": "Produto criado com sucesso",
                "id": str(result.inserted_id)
            }), 201
            
        except Exception as e:
            print(f"Erro ao criar item: {e}")
            return jsonify({"error": "Erro ao criar item"}), 500
    

# * ========================================== PUT ========================================== *
@items_blueprint.route("/items/<id>", methods=["PUT"])
def update_item(id):
    """Atualiza item existente"""
    token_required = token_required_import()
    
    @token_required
    def _update(current_user):
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Dados inválidos"}), 400
            
            # ver se o item existe e pertence ao usuário
            items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
            item = items_collection.find_one({"_id": ObjectId(id)})
            
            if not item:
                return jsonify({"error": "Product not found"}), 404
            
            if item["seller_id"] != current_user["_id"]:
                return jsonify({"error": "Não autorizado"}), 403
            
            # tirar campos que não devem atualizar
            data.pop("_id", None)
            data.pop("seller_id", None)
            data.pop("created_at", None)
            
            result = items_collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": data}
            )
            
            if result.matched_count == 0:
                return jsonify({"error": "Product not found"}), 404
            
            return jsonify({"message": "Produto atualizado com sucesso"}), 200
            
        except Exception as e:
            print(f"Erro ao atualizar item: {e}")
            return jsonify({"error": "Erro ao atualizar"}), 400
    
    return _update()




# * ========================================== DELETE ========================================== *
@items_blueprint.route("/items/<id>", methods=["DELETE"])
def delete_item(id):
    """Remove item"""
    token_required = token_required_import()
    
    @token_required
    def _delete(current_user):
        try:
            items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
            item = items_collection.find_one({"_id": ObjectId(id)})
            
            if not item:
                return jsonify({"error": "Product not found"}), 404
            
            if item["seller_id"] != current_user["_id"]:
                return jsonify({"error": "Não autorizado"}), 403
            
            result = items_collection.delete_one({"_id": ObjectId(id)})
            
            if result.deleted_count == 0:
                return jsonify({"error": "Product not found"}), 404
            
            return jsonify({"message": "Produto removido com sucesso"}), 200
            
        except Exception as e:
            print(f"Erro ao deletar item: {e}")
            return jsonify({"error": "Erro ao deletar"}), 400
    
    return _delete()