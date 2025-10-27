from flask import Blueprint, request, jsonify, current_app
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import os
from functools import wraps
from utils import bcrypt
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import requests

auth_blueprint = Blueprint("auth", __name__)

def get_collection(name):
    return current_app.db[name]


# ============================ ROTAS ============================
@auth_blueprint.route("/register", methods=["POST"])
def register():
    try: 
        data = request.get_json()
        campos_obrigatorios = ["email", "password", "name", 'satus']
        #todo verificar se todos os campos obrigatórios do diagrama estão aqui
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
            "password": bcrypt.generate_password_hash(data["password"]),
            "name": data["name"],
            "phone": data.get("phone"),
            "created_at": datetime.now(),
            "status": data.get("status"),
            "is_active": True
        }
        
        result = users_collection.insert_one(user)
        user = users_collection.find_one({"email": data["email"]})
        token = create_access_token(identity=user['_id'].__str__())
               
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
        
        if not user or not bcrypt.check_password_hash(user["password"], data["password"]):
            return jsonify({"error": "Email ou senha incorretos"}), 401
        
        if not user.get("is_active", True):
            return jsonify({"error": "Usuário inativo"}), 401
        
        token = create_access_token(identity=user['_id'].__str__())
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


@auth_blueprint.route("/adm", methods=["GET"])
@jwt_required()
def adm_route():
    current_user_email = get_jwt_identity() # pega o email do user logado a partir do token
    return jsonify(logged_in_as=current_user_email), 200


# ============================ CEP API ROUTE ============================

@auth_blueprint.route("/cep", methods=["POST"])
def buscar_cep():
    try:
        data = request.get_json()
        cep = data.get("cep")

        if not cep:
            return jsonify({"erro": "CEP não informado"}), 400

        url = "https://api.cep.rest/"
        payload = {"cep": cep}
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500



#TODO Implementar as rotas de user/<user_id>; user/<user_id>/compras, user/<user_id>/vendas;


# # ==================== PERFIL ====================
# @auth_blueprint.route("/user/<user_id>", methods=["GET"])
# @token_required
# def get_profile(current_user):
#     return jsonify(current_user), 200


# @auth_blueprint.route("/user/<user_id>", methods=["PUT"])
# @token_required
# def update_profile(current_user):
#     try:
#         data = request.get_json()
        
#         allowed_fields = ["name", "phone"]
#         update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
#         if not update_data:
#             return jsonify({"error": "Nenhum campo válido para atualizar"}), 400
        
#         users_collection = get_collection(os.getenv("COLLECTION_USERS"))
#         users_collection.update_one(
#             {"_id": ObjectId(current_user["_id"])},
#             {"$set": update_data}
#         )
        
#         return jsonify({"message": "Perfil atualizado com sucesso"}), 200
        
#     except Exception as e:
#         print(f"Erro ao atualizar perfil: {e}")
#         return jsonify({"error": "Erro ao atualizar perfil"}), 500


# # ==================== ALTERAR SENHA ====================
# @auth_blueprint.route("/change-password", methods=["PUT"])
# @token_required
# def change_password(current_user):
#     try:
#         data = request.get_json()
        
#         if not data.get("old_password") or not data.get("new_password"):
#             return jsonify({"error": "Senhas antigas e nova obrigatórias"}), 400
        
#         if len(data["new_password"]) < 6:
#             return jsonify({"error": "Nova senha deve ter pelo menos 6 caracteres"}), 400
        
#         users_collection = get_collection(os.getenv("COLLECTION_USERS"))
#         user = users_collection.find_one({"_id": ObjectId(current_user["_id"])})
        
#         if not check_password_hash(user["password"], data["old_password"]):
#             return jsonify({"error": "Senha antiga incorreta"}), 401
        
#         new_hash = generate_password_hash(data["new_password"])
#         users_collection.update_one(
#             {"_id": ObjectId(current_user["_id"])},
#             {"$set": {"password": new_hash}}
#         )
        
#         return jsonify({"message": "Senha alterada com sucesso"}), 200
        
#     except Exception as e:
#         print(f"Erro ao alterar senha: {e}")
#         return jsonify({"error": "Erro ao alterar senha"}), 500
    