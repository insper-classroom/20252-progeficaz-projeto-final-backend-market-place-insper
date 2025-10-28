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
        data = request.get_json() or {}

        # campos obrigatórios no nível raiz
        campos_obrigatorios = ["email", "password", "name"]
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({"error": f"Campo '{campo}' é obrigatório"}), 400

        # valida email Insper (aceita ambos os domínios já que o front valida ambos)
        email = str(data.get("email", "")).strip()
        if not (email.endswith("@al.insper.edu.br") or email.endswith("@insper.edu.br")):
            return jsonify({"error": "E-mail deve ser do Insper (@al.insper.edu.br ou @insper.edu.br)"}), 400

        if len(data.get("password", "")) < 6:
            return jsonify({"error": "Senha deve ter pelo menos 6 caracteres"}), 400

        # endereco esperado como subdocumento
        endereco = data.get("endereco") or {}
        if not isinstance(endereco, dict):
            return jsonify({"error": "Campo 'endereco' inválido ou ausente"}), 400

        # limpa CEP: só dígitos (mantemos só a limpeza — se necessário, só retiramos caracteres no CEP)
        raw_cep = str(endereco.get("cep") or "")
        cep_clean = "".join([c for c in raw_cep if c.isdigit()])
        if not cep_clean or len(cep_clean) != 8:
            return jsonify({"error": "CEP inválido. Deve conter 8 dígitos."}), 400

        users_collection = get_collection(os.getenv("COLLECTION_USERS"))

        if users_collection.find_one({"email": email}):
            return jsonify({"error": "Email já cadastrado"}), 409

        # normaliza strings simples (remover espaços extras)
        def clean(s):
            try:
                return str(s).strip()
            except:
                return ""

        endereco_normalizado = {
            "cep": cep_clean,
            "logradouro": clean(endereco.get("logradouro")),
            "numero": clean(endereco.get("numero")),
            "complemento": clean(endereco.get("complemento")),
            "bairro": clean(endereco.get("bairro")),
            "cidade": clean(endereco.get("cidade")),
            "estado": clean(endereco.get("estado")),
        }

        user = {
            "email": email,
            "password": bcrypt.generate_password_hash(data["password"]),
            "name": clean(data.get("name")),
            "phone": data.get("phone"),
            "created_at": datetime.now(),
            "status": data.get("status"),
            "is_active": True,
            "endereco": endereco_normalizado
        }

        result = users_collection.insert_one(user)
        user = users_collection.find_one({"_id": result.inserted_id})
        token = create_access_token(identity=str(user['_id']))

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
        data = request.get_json() or {}
        raw_cep = data.get("cep")
        if not raw_cep:
            return jsonify({"erro": "CEP não informado"}), 400

        # limpa CEP: só dígitos
        cep = "".join([c for c in str(raw_cep) if c.isdigit()])

        if len(cep) != 8:
            return jsonify({"erro": "CEP inválido. Deve conter 8 dígitos."}), 400

        # ViaCEP (GET) - resposta JSON consistente
        url = f"https://viacep.com.br/ws/{cep}/json/"

        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return jsonify({"erro": f"Erro ao consultar ViaCEP (status {resp.status_code})"}), 502

        data_cep = resp.json()

        # ViaCEP devolve {"erro": true} quando não encontra
        if data_cep.get("erro"):
            return jsonify({"erro": "CEP não encontrado"}), 404

        # mapeia para um formato previsível
        resultado = {
            "cep": data_cep.get("cep", ""),
            "logradouro": data_cep.get("logradouro", ""),
            "bairro": data_cep.get("bairro", ""),
            "cidade": data_cep.get("localidade", ""),
            "estado": data_cep.get("uf", "")
        }

        return jsonify(resultado), 200

    except Exception as e:
        print(f"Erro buscar_cep: {e}")
        return jsonify({"erro": str(e)}), 500


# # ==================== PERFIL ====================
@auth_blueprint.route("/user/<user_id>", methods=["GET"])
@jwt_required()
def get_profile(user_id):
    try:
        user_collection = get_collection(os.getenv("COLLECTION_USERS"))
        doc = user_collection.find_one({"_id": ObjectId(user_id)})
        if not doc:
            return jsonify({"error": "User not found"}), 404
        doc["_id"] = str(doc["_id"])
        return jsonify(doc), 200
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return jsonify({"error": "ID inválido"}), 400


# @auth_blueprint.route("/user/<user_id>", methods=["PUT"])
# @jwt_required()
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

# # ==================== VENDAS ====================
@auth_blueprint.route("/user/<user_id>/vendas", methods=["GET"])
@jwt_required()
def get_vendas(user_id):
    collection = get_collection(os.getenv("COLLECTION_ITEMS"))

    avenda = list(collection.find({"seller_id": user_id, "status": "avenda"}))
    andamento = list(collection.find({"seller_id": user_id, "status": "emandamento"}))
    finalizada = list(collection.find({"seller_id": user_id, "status": "finalizada"}))

    def convert_ids(lista):
        for item in lista:
            item["_id"] = str(item["_id"])
            if "seller_id" in item and item["seller_id"] is not None:
                item["seller_id"] = str(item["seller_id"])
        return lista

    return {
        "avenda": convert_ids(avenda),
        "andamento": convert_ids(andamento),
        "finalizada": convert_ids(finalizada),
    }

# # ==================== COMPRAS ====================
@auth_blueprint.route("/user/<user_id>/compras", methods=["GET"])
@jwt_required()
def get_compras(user_id):
    collection = get_collection(os.getenv("COLLECTION_ITEMS"))
    
    andamento = list(collection.find({"buyer_id": user_id, "status": "emandamento"}))
    finalizada = list(collection.find({"buyer_id": user_id, "status": "finalizada"}))

    def convert_ids(lista):
        for item in lista:
            item["_id"] = str(item["_id"])
            if "buyer_id" in item and item["buyer_id"] is not None:
                item["buyer_id"] = str(item["buyer_id"])
        return lista

    return {
        "andamento": convert_ids(andamento),
        "finalizada": convert_ids(finalizada),
    }

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