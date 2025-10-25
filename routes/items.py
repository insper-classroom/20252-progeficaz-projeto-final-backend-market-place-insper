from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity # o primeiro pra sinalizar que precisa do token e o segundo pra pegar o user id do token
from datetime import datetime
from bson.objectid import ObjectId # serve para identificar itemumentos no MongoDB
import os
from utils import upload_multiple_images, delete_image, upload_image

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

def get_items_from_db():
    collection = get_collection(os.getenv("COLLECTION_ITEMS"))
    items = list(collection.find({}))
    # Convertendo ObjectId para string para JSON serializable
    for item in items:
        item["_id"] = str(item["_id"])
        item["seller_id"] = str(item["seller_id"])
    return items  

def get_users_from_db():
    collection = get_collection(os.getenv("COLLECTION_USERS"))
    users = list(collection.find({}))
    for user in users:
        user["_id"] = str(user["_id"])
    return users  


# ~=~ ROTAS ~=~

# ========================================== GET ========================================== *
@items_blueprint.route("/items", methods=["GET"])
def get_items():
    """Lista todos os itens"""
    print(f'Método: {request.method}')
    try:
        items = get_items_from_db()
        print(f'Itens encontrados: {len(items)}')
        return jsonify(items), 200
    except Exception as e:
        print(f"Erro ao listar itens: {e}")
        return jsonify({"error": "Erro ao listar itens"}), 500 # erro interno do serv


@items_blueprint.route("/items/<id>", methods=["GET"])
def get_item(id):
    """Busca item por ID"""
    try:
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        item = items_collection.find_one({"_id": ObjectId(id)})
        
        if not item:
            return jsonify({"error": "Product not found"}), 404
        # ObjectId -> string
        item["_id"] = str(item["_id"])
        if "seller_id" in item:
            item["seller_id"] = str(item["seller_id"])
        
        return jsonify(item), 200
    except Exception as e:
        print(f"Erro ao buscar item: {e}")
        return jsonify({"error": "ID inválido"}), 400 # bad request
    

@items_blueprint.route("/items/category/<category>", methods=["GET"])
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


@items_blueprint.route("/items/seller/<seller_id>", methods=["GET"])
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


# ========================================== POST ========================================== 
@items_blueprint.route("/items", methods=["POST"])
@jwt_required()
def create_item():
    """Cria novo item com imagens"""
    try:
        # ve se tem arquivos (form-data) ou JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # form-data
            data = request.form.to_dict()
            print("=" * 50)
            print("DADOS RECEBIDOS:", data)
            print("=" * 50)
            
            # price -> float
            if 'price' in data:
                data['price'] = float(data['price'])
            
            # upld de imagens
            images = []
            for key in request.files:
                file = request.files[key]
                if file and file.filename:  # ve se tem arquivo
                    print(f"Fazendo upload de: {file.filename}")
                    image_url = upload_image(file)
                    if image_url:
                        images.append(image_url)
                        print(f"Upload bem-sucedido: {image_url}")
                    else:
                        print(f"Falha no upload de: {file.filename}")
            
            data["images"] = images
            print(f"Total de imagens: {len(images)}")
        else:
            # JSON puro (sem imagens)
            data = request.get_json()
            if not data:
                return jsonify({"error": "Nenhum dado enviado"}), 400
        
        # Validações obrigatórias
        required_fields = {
            "title": "Título é obrigatório",
            "description": "Descrição é obrigatória",
            "price": "Preço é obrigatório",
            "category": "Categoria é obrigatória"
        }
        
        for field, error_message in required_fields.items():
            if not data.get(field):
                return jsonify({"error": error_message}), 400
        
        # validação
        if not data.get("title"):
            return jsonify({"error": "Título é obrigatório"}), 400
        
        if data.get("price", -1) <= 0:
            return jsonify({"error": "Preço deve ser maior que zero"}), 400
        
        # pega usuário autenticado
        current_user_id = get_jwt_identity()
        users_collection = get_collection(os.getenv("COLLECTION_USERS"))
        current_user = users_collection.find_one({"_id": ObjectId(current_user_id)})
        
        if not current_user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # metadados
        data["seller_id"] = str(current_user["_id"])
        data["created_at"] = datetime.now()
        data["status"] = data.get("status", "Ativo")
        data.setdefault("boosted", False)
        print("=" * 50)
        print("DOCUMENTO FINAL A SER INSERIDO:")
        for key, value in data.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
        print("=" * 50)
        
        # bota no banco
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        result = items_collection.insert_one(data)
        
        return jsonify({
            "message": "Produto criado com sucesso",
            "id": str(result.inserted_id),
            "images": data.get("images", [])
        }), 201
        
    except Exception as e:
        print(f"Erro ao criar item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro ao criar item: {str(e)}"}), 500


# ========================================== PUT ========================================== 
@items_blueprint.route("/items/<id>", methods=["PUT"])
@jwt_required()
def update_item(id):
    """Atualiza existente"""
    try:
        current_user_id = get_jwt_identity()
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        item = items_collection.find_one({"_id": ObjectId(id)})
        
        if not item:
            return jsonify({"error": "Product not found"}), 404
        
        if str(item["seller_id"]) != str(current_user_id):
            return jsonify({"error": "Não autorizado"}), 403
        
        # Verifica se tem arquivos
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            
            if 'price' in data:
                data['price'] = float(data['price'])
            
            # Upload de novas imagens
            new_images = []
            for key in request.files:
                file = request.files[key]
                if file and file.filename:
                    image_url = upload_image(file)
                    if image_url:
                        new_images.append(image_url)
            
            # Mantém imagens antigas e adiciona novas
            existing_images = item.get("images", [])
            data["images"] = existing_images + new_images
        else:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Dados inválidos"}), 400
        
        # Remove campos que não devem ser atualizados
        data.pop("_id", None)
        data.pop("seller_id", None)
        data.pop("created_at", None)
        
        result = items_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404
        
        return jsonify({
            "message": "Produto atualizado com sucesso",
            "images": data.get("images", [])
        }), 200
        
    except Exception as e:
        print(f"Erro ao atualizar item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erro ao atualizar"}), 400


# ========================================== DELETE ========================================== 
@items_blueprint.route("/items/<id>", methods=["DELETE"])
@jwt_required()
def delete_item(id):
    """Remove item e suas imagens do Cloudinary"""
    try:
        current_user_id = get_jwt_identity()
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        
        item = items_collection.find_one({"_id": ObjectId(id)})
        if not item:
            return jsonify({"error": "Product not found"}), 404
        
        if str(item["seller_id"]) != str(current_user_id):
            return jsonify({"error": "Não autorizado"}), 403
        
        # Deletar imagens do Cloudinary
        if "images" in item and item["images"]:
            print(f"Deletando {len(item['images'])} imagens...")
            for image_url in item["images"]:
                success = delete_image(image_url)
                if success:
                    print(f"imagem deletada: {image_url}")
                else:
                    print(f"Falha ao deletar: {image_url}")
        
        # Deletar item do banco
        result = items_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Product not found"}), 404
        
        return jsonify({"message": "Produto deletado com sucesso"}), 200
    
    except Exception as e:
        print(f"Erro ao deletar item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erro ao deletar"}), 400


# ========================================== ROTA EXTRA: Deletar imagem específica ========================================== 
@items_blueprint.route("/items/<id>/images", methods=["DELETE"])
@jwt_required()
def delete_item_image(id):
    """Remove uma imagem específica do item"""
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        
        if not image_url:
            return jsonify({"error": "URL da imagem não fornecida"}), 400
        
        current_user_id = get_jwt_identity()
        items_collection = get_collection(os.getenv("COLLECTION_ITEMS"))
        
        item = items_collection.find_one({"_id": ObjectId(id)})
        if not item:
            return jsonify({"error": "Product not found"}), 404
        
        if str(item["seller_id"]) != str(current_user_id):
            return jsonify({"error": "Não autorizado"}), 403
        
        # Remove a imagem da lista
        if "images" in item and image_url in item["images"]:
            # Deleta do Cloudinary
            delete_image(image_url)
            
            # Remove do array
            items_collection.update_one(
                {"_id": ObjectId(id)},
                {"$pull": {"images": image_url}}
            )
            
            return jsonify({"message": "imagem removida com sucesso"}), 200
        else:
            return jsonify({"error": "imagem não encontrada"}), 404
            
    except Exception as e:
        print(f"Erro ao remover imagem: {e}")
        return jsonify({"error": "Erro ao remover imagem"}), 400