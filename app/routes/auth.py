from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from mongoengine.errors import NotUniqueError, ValidationError, DoesNotExist
from ..models import User, Product
from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    email = data.get("email")
    name = data.get("name", "")
    password = data.get("password")
    cellphone = data.get("cellphone")

    if not email or not password:
        return jsonify({"error": "email e password são obrigatórios"}), 400

    if not cellphone:
        return jsonify({"error": "cellphone é obrigatório"}), 400

    try:
        u = User(email=email, name=name, cellphone=cellphone)
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

@bp.route("/me/sales", methods=["GET"])
@jwt_required()
def my_sales():
    """Retorna todos os produtos que o usuário vendeu (onde ele é owner e tem buyer)"""
    user_id = get_jwt_identity()
    try:
        user = User.objects.get(id=user_id)
        # Busca produtos onde o usuário é owner e já tem um buyer (foi vendido)
        sales = Product.objects(owner=user, buyer__ne=None)

        sales_list = []
        for product in sales:
            sale_data = product.to_dict()
            # Adiciona informações da venda
            sale_data['sale_info'] = {
                'buyer': product.buyer.to_dict() if product.buyer else None,
                'sold_at': product.created_at.isoformat()  # Pode adicionar um campo de data de venda se quiser
            }
            sales_list.append(sale_data)

        return jsonify({
            "total": len(sales_list),
            "sales": sales_list
        }), 200
    except DoesNotExist:
        return jsonify({"error": "usuário não encontrado"}), 404

@bp.route("/me/purchases", methods=["GET"])
@jwt_required()
def my_purchases():
    """Retorna todos os produtos que o usuário comprou (onde ele é buyer)"""
    user_id = get_jwt_identity()
    try:
        user = User.objects.get(id=user_id)
        # Busca produtos onde o usuário é buyer
        purchases = Product.objects(buyer=user)

        purchases_list = []
        for product in purchases:
            purchase_data = product.to_dict()
            # Adiciona informações da compra
            purchase_data['purchase_info'] = {
                'seller': product.owner.to_dict() if product.owner else None,
                'purchased_at': product.created_at.isoformat()
            }
            purchases_list.append(purchase_data)

        return jsonify({
            "total": len(purchases_list),
            "purchases": purchases_list
        }), 200
    except DoesNotExist:
        return jsonify({"error": "usuário não encontrado"}), 404

@bp.route("/me/favorites", methods=["GET"])
@jwt_required()
def my_favorites():
    """Retorna todos os produtos favoritos do usuário"""
    user_id = get_jwt_identity()
    try:
        user = User.objects.get(id=user_id)

        # Converte a lista de referências em dicionários
        favorites_list = [product.to_dict() for product in user.favorites if product]

        return jsonify({
            "total": len(favorites_list),
            "favorites": favorites_list
        }), 200
    except DoesNotExist:
        return jsonify({"error": "usuário não encontrado"}), 404
