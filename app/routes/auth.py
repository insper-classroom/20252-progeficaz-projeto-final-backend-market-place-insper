from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from mongoengine.errors import NotUniqueError, ValidationError, DoesNotExist
from ..models import User
from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    email = data.get("email")
    name = data.get("name", "")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email e password são obrigatórios"}), 400

    try:
        u = User(email=email, name=name)
        u.set_password(password)
        u.save()
        return jsonify({"message": "usuário criado", "user": u.to_dict()}), 201
    except NotUniqueError:
        return jsonify({"error": "email já cadastrado"}), 409
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

@bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email e password são obrigatórios"}), 400

    try:
        u = User.objects.get(email=email)
        if not u.check_password(password):
            return jsonify({"error": "credenciais inválidas"}), 401
        access_token = create_access_token(identity=str(u.id))
        return jsonify({"access_token": access_token}), 200
    except DoesNotExist:
        return jsonify({"error": "credenciais inválidas"}), 401

@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    try:
        u = User.objects.get(id=user_id)
        return jsonify(u.to_dict()), 200
    except DoesNotExist:
        return jsonify({"error": "usuário não encontrado"}), 404
