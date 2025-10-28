from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity # o primeiro pra sinalizar que precisa do token e o segundo pra pegar o user id do token
from datetime import datetime
from bson.objectid import ObjectId # serve para identificar documentos no MongoDB
from werkzeug.utils import secure_filename
import os

items_blueprint = Blueprint("items", __name__)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
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

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def token_required_import(): # importa o decorador token_required 
    from routes.auth import token_required
    return token_required

def get_items_from_db():
    collection = get_collection(os.getenv("COLLECTION_ITEMS"))
    
    emdestaque = list(collection.find({"boosted": True}))
    eletronicos = list(collection.find({"category": "Eletrônicos"}))
    eletrodomesticos = list(collection.find({"category": "Eletrodomésticos"}))
    moveis = list(collection.find({"category": "Móveis"}))
    outros = list(collection.find({"category": "Outros"}))
    
    # Função auxiliar pra converter ObjectId -> str
    def convert_ids(lista):
        for item in lista:
            item["_id"] = str(item["_id"])
            if "seller_id" in item and item["seller_id"] is not None:
                item["seller_id"] = str(item["seller_id"])
        return lista

    return {
        "emDestaque": convert_ids(emdestaque),
        "eletronicos": convert_ids(eletronicos),
        "eletrodomesticos": convert_ids(eletrodomesticos),
        "moveis": convert_ids(moveis),
        "outros": convert_ids(outros),
    }

def get_users_from_db():
    collection = get_collection(os.getenv("COLLECTION_USERS"))
    users = list(collection.find({}))
    for user in users:
        user["_id"] = str(user["_id"])
    return users  


# ~=~ ROTAS ~=~

# ========================================== GET ========================================== *
#TODO fazer essa rota listar: emDestaque, eletronicos, eletrodomesticos, moveis, outros
#TODO enviar arrays para o frontend com os produtos em destaque e por categoria

@items_blueprint.route("/", methods=["GET"])
def get_items():
    """Lista todos os itens por categoria"""
    try:
        items = get_items_from_db()
        return jsonify(items), 200
    except Exception as e:
        print(f"Erro ao listar itens: {e}")
        return jsonify({"error": "Erro ao listar itens"}), 500


@items_blueprint.route("/<id>", methods=["GET"])
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
    

@items_blueprint.route("/category/<category>", methods=["GET"])
def get_items_by_category(category):
    """Lista itens por categoria"""
    try:
        items = get_items_from_db()
        # filtra os itens pela categoria
        filtered_items = [item for item in items if item.get("category") == category]
        return jsonify(filtered_items), 200
    except Exception as e:
        print(f"Erro ao buscar por categoria: {e}")
        return jsonify({"error": "Erro ao buscar itens"}), 500


@items_blueprint.route("/seller/<seller_id>", methods=["GET"])
def get_items_by_seller(seller_id):
    """Lista itens por vendedor"""
    try:
        items = get_items_from_db()
        # filtra os itens pelo seller_id
        filtered_items = [item for item in items if item.get("seller_id") == seller_id]
        return jsonify(filtered_items), 200
    except Exception as e:
        print(f"Erro ao buscar por vendedor: {e}")
        return jsonify({"error": "Erro ao buscar itens"}), 500


@items_blueprint.route("/seller/phone/<seller_id>", methods=["GET"])
def get_seller_phone(seller_id):
    """Retorna o número de telefone do vendedor"""
    try:
        users_collection = get_collection(os.getenv("COLLECTION_USERS"))
        seller = users_collection.find_one({"_id": ObjectId(seller_id)})
        
        if not seller:
            return jsonify({"error": "Vendedor não encontrado"}), 404
            
        # Assumindo que o número está armazenado no campo 'phone'
        phone = seller.get("phone", "Número não disponível")
        
        return jsonify({
            "seller_id": str(seller["_id"]),
            "phone": phone
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar número do vendedor: {e}")
        return jsonify({"error": "Erro ao buscar número do vendedor"}), 500


# ========================================== POST ========================================== *
@items_blueprint.route("/", methods=["POST"])
@jwt_required()
def create_item():
    """Cria novo item com upload de imagem"""
    try:
        # Obtém dados do formulário
        title = request.form.get("title")
        description = request.form.get("description")
        price = float(request.form.get("price", 0))
        category = request.form.get("category")
        condition = request.form.get("condition")
        image = request.files.get("image")

        if not title or price <= 0 or not image:
            return jsonify({"error": "Dados inválidos"}), 400

        if not allowed_file(image.filename):
            return jsonify({"error": "Formato de imagem inválido"}), 400

        # Cria pasta se não existir
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Salva a imagem localmente
        filename = secure_filename(image.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image.save(filepath)

        # Gera a URL acessível da imagem
        image_url = f"http://localhost:5000/{UPLOAD_FOLDER}/{filename}"

        # Pega o usuário autenticado
        current_user_id = get_jwt_identity()
        users_collection = get_collection(os.getenv("COLLECTION_USERS"))
        current_user = users_collection.find_one({"_id": ObjectId(current_user_id)})

        # Salva o produto no banco
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        new_item = {
            "title": title,
            "description": description,
            "price": price,
            "category": category,
            "condition": condition,
            "images": [image_url],  # 👈 importante: campo que o front vai usar
            "seller_id": current_user["_id"],
            "created_at": datetime.now(),
            "status": "Ativo",
        }

        result = items_collection.insert_one(new_item)

        return jsonify({
            "message": "Produto criado com sucesso",
            "id": str(result.inserted_id),
            "image_url": image_url
        }), 201

    except Exception as e:
        print(f"Erro ao criar item: {e}")
        return jsonify({"error": "Erro ao criar item"}), 500
    
@items_blueprint.route("/uploads/<path:filename>")
def serve_uploaded_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ========================================== PUT ========================================== *
@items_blueprint.route("item/<id>", methods=["PUT"])
@jwt_required() 
def update_item(id):
    """Atualiza item existente"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400
        
        # ver se o item existe e pertence ao usuário
        current_user_id = get_jwt_identity() # pega o id do user logado a partir do token
        
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        item = items_collection.find_one({"_id": ObjectId(id)})
        
        if not item:
            return jsonify({"error": "Product not found"}), 404
        
        if str(item["seller_id"]) != str(current_user_id):
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
    

# ========================================== DELETE ========================================== *
@items_blueprint.route("/<id>", methods=["DELETE"])
@jwt_required()
def delete_item(id):
    """Remove item"""
    try:
        #deletar item
        current_user_id = get_jwt_identity() # pega o id do user logado a partir do token
        
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        
        item = items_collection.find_one({"_id": ObjectId(id)})
        if not item:
            return jsonify({"error": "Product not found"}), 404
        
        if str(item["seller_id"]) != str(current_user_id):
            return jsonify({"error": "Não autorizado"}), 403
        
        result = items_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Product not found"}), 404
        return jsonify({"message": "Produto deletado com sucesso"}), 200
    
    except Exception as e:
        print(f"Erro ao deletar item: {e}")
        return jsonify({"error": "Erro ao deletar"}), 400

