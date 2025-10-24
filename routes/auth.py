from flask import Blueprint, request, jsonify, current_app
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import os
import jwt
from werkzeug.security import generate_password_hash, check_password_hash   
from functools import wraps

auth_blueprint = Blueprint("auth", __name__)

def get_collection(name):
    return current_app.db[name]


# ============================ DECORADORES ============================
def token_required(f):
    """Decorator para proteger rotas que precisam de autenticação
    Como funciona:
    1. Verifica se o token tá no header Authorization
    2. Decodifica o token c a SECRET_KEY
    3. Busca o user no db usando o user_id do token
    4. Chama a função da rota passando o user
    """
    
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token não existe!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
                
            data = jwt.decode(token, os.getenv("SECRET_KEY", "dev-secret-key"), algorithms=["HS256"])
            
            users_collection = get_collection(os.getenv("COLLECTION_USERS"))
            current_user = users_collection.find_one({"_id": ObjectId(data['user_id'])})

            if not current_user:
                return jsonify({'message': 'Usuário não encontrado!'}), 401
            
            current_user.pop("password", None)
            current_user["_id"] = str(current_user["_id"])  # Converte para string
        
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido!'}), 401
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return jsonify({'message': 'Erro na autenticação!'}), 401
        
        # CORREÇÃO: passa current_user como argumento posicional
        return f(current_user, *args, **kwargs)
    
    return decorated


# ============================ ROTAS ============================
@auth_blueprint.route("/register", methods=["POST"])
def register():
    try: 
        data = request.get_json()
        campos_obrigatorios = ["email", "password", "name"]
        for campo in campos_obrigatorios:
            if campo not in data:
                return jsonify({"error": f"Campo '{campo}' é obrigatório"}), 400
        
        if not data['email'].endswith("@al.insper.edu.br"):
            return jsonify({"error": "E-mail deve ser do Insper"}), 400
        
        if len(data["password"]) < 6:
            return jsonify({"error": "Senha deve ter pelo menos 6 caracteres"}), 400
            
        users_collection = get_collection(os.getenv("COLLECTION_USERS"))
        if users_collection.find_one({"email": data["email"]}):
            return jsonify({"error": "Email já cadastrado"}), 409
            
        user = {
            "email": data["email"],
            "password": generate_password_hash(data["password"]),
            "name": data["name"],
            "phone": data.get("phone"),
            "created_at": datetime.now(),
            "is_active": True
        }
        
        result = users_collection.insert_one(user)
        
        token = jwt.encode({ 
            'user_id': str(result.inserted_id), 
            'exp': datetime.now() + timedelta(days=7)
        }, os.getenv("SECRET_KEY", "dev-secret-key"), algorithm="HS256")
            
        return jsonify({
            "message": "Usuário criado com sucesso",
            "token": token,
            "user": {
                "id": str(result.inserted_id),
                "email": user["email"],
                "name": user["name"]
            }
        }), 201
            
    except Exception as e:
        print(f"Erro no registro: {e}")
        return jsonify({"error": "Erro ao criar usuário"}), 500


# ============================ LOGIN ============================
@auth_blueprint.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email e senha obrigatórios"}), 400
        
        users_collection = get_collection(os.getenv("COLLECTION_USERS"))
        user = users_collection.find_one({"email": data["email"]})
        
        if not user or not check_password_hash(user["password"], data["password"]):
            return jsonify({"error": "Email ou senha incorretos"}), 401
        
        if not user.get("is_active", True):
            return jsonify({"error": "Usuário inativo"}), 401
        
        token = jwt.encode({
            'user_id': str(user["_id"]),
            'exp': datetime.now() + timedelta(days=7)
        }, os.getenv("SECRET_KEY", "dev-secret-key"), algorithm="HS256")
        
        return jsonify({
            "message": "Login realizado com sucesso",
            "token": token,
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user["name"]
            }
        }), 200
        
    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({"error": "Erro ao realizar login"}), 500


# ==================== PERFIL ====================
@auth_blueprint.route("/me", methods=["GET"])
@token_required
def get_profile(current_user):
    return jsonify(current_user), 200


@auth_blueprint.route("/me", methods=["PUT"])
@token_required
def update_profile(current_user):
    try:
        data = request.get_json()
        
        allowed_fields = ["name", "phone"]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({"error": "Nenhum campo válido para atualizar"}), 400
        
        users_collection = get_collection(os.getenv("COLLECTION_USERS"))
        users_collection.update_one(
            {"_id": ObjectId(current_user["_id"])},
            {"$set": update_data}
        )
        
        return jsonify({"message": "Perfil atualizado com sucesso"}), 200
        
    except Exception as e:
        print(f"Erro ao atualizar perfil: {e}")
        return jsonify({"error": "Erro ao atualizar perfil"}), 500


# ==================== ALTERAR SENHA ====================
@auth_blueprint.route("/change-password", methods=["PUT"])
@token_required
def change_password(current_user):
    try:
        data = request.get_json()
        
        if not data.get("old_password") or not data.get("new_password"):
            return jsonify({"error": "Senhas antigas e nova obrigatórias"}), 400
        
        if len(data["new_password"]) < 6:
            return jsonify({"error": "Nova senha deve ter pelo menos 6 caracteres"}), 400
        
        users_collection = get_collection(os.getenv("COLLECTION_USERS"))
        user = users_collection.find_one({"_id": ObjectId(current_user["_id"])})
        
        if not check_password_hash(user["password"], data["old_password"]):
            return jsonify({"error": "Senha antiga incorreta"}), 401
        
        new_hash = generate_password_hash(data["new_password"])
        users_collection.update_one(
            {"_id": ObjectId(current_user["_id"])},
            {"$set": {"password": new_hash}}
        )
        
        return jsonify({"message": "Senha alterada com sucesso"}), 200
        
    except Exception as e:
        print(f"Erro ao alterar senha: {e}")
        return jsonify({"error": "Erro ao alterar senha"}), 500
    