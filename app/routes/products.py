from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError
from mongoengine.queryset.visitor import Q
from ..models import Product, User
import secrets
import cloudinary.uploader
import base64


bp = Blueprint("products", __name__, url_prefix="/products")



@bp.route("", methods=["GET"])
def list_products():
    """
    Lista produtos disponíveis (não comprados e não em negociação).
    Query params:
        - q: string de busca (busca em title e description)
    """
    search_query = request.args.get("q", "").strip()

    # Busca apenas produtos que ainda não foram "reservados" por um comprador
    query = Product.objects(buyer=None)

    # Se houver termo de busca, filtra por title ou description
    if search_query:
        query = query.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    products = query.order_by("-created_at")
    return jsonify([p.to_dict() for p in products]), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_product():
    """
    Cria um novo produto.
    Requer autenticação.
    Body (JSON):
        - title: string (obrigatório)
        - description: string (opcional)
        - price: float (obrigatório, >= 0)
        - category: string (obrigatório, valores: "eletrodomésticos", "eletrônicos", "móveis", "outros")
        - estado_de_conservacao: string (obrigatório, valores: "novo", "seminovo", "usado")
    """
    user_id = get_jwt_identity()
    data = request.json or {}

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    price = data.get("price")
    category = data.get("category", "").strip()
    estado_de_conservacao = data.get("estado_de_conservacao", "").strip()

    # Validações básicas
    if not title:
        return jsonify({"error": "title é obrigatório"}), 400

    if price is None:
        return jsonify({"error": "price é obrigatório"}), 400

    if not category:
        return jsonify({"error": "category é obrigatório"}), 400

    if not estado_de_conservacao:
        return jsonify({"error": "estado_de_conservacao é obrigatório"}), 400

    # Validação de valores permitidos
    categorias_validas = ["eletrodomésticos", "eletrônicos", "móveis", "outros"]
    if category not in categorias_validas:
        return jsonify({"error": f"category deve ser um dos seguintes: {', '.join(categorias_validas)}"}), 400

    estados_validos = ["novo", "seminovo", "usado"]
    if estado_de_conservacao not in estados_validos:
        return jsonify({"error": f"estado_de_conservacao deve ser um dos seguintes: {', '.join(estados_validos)}"}), 400

    try:
        price = float(price)
    except (ValueError, TypeError):
        return jsonify({"error": "price deve ser um número"}), 400

    if price < 0:
        return jsonify({"error": "price deve ser maior ou igual a 0"}), 400

    try:
        user = User.objects.get(id=user_id)
        product = Product(
            title=title,
            description=description,
            price=price,
            category=category,
            estado_de_conservacao=estado_de_conservacao,
            owner=user
        )
        product.save()
        return jsonify({"message": "produto criado", "product": product.to_dict()}), 201
    except DoesNotExist:
        return jsonify({"error": "usuário não encontrado"}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<product_id>", methods=["GET"])
def get_product(product_id):
    """
    Retorna detalhes de um produto específico.
    """
    try:
        product = Product.objects.get(id=product_id)
        return jsonify(product.to_dict()), 200
    except DoesNotExist:
        return jsonify({"error": "produto não encontrado"}), 404
    except ValidationError:
        return jsonify({"error": "ID inválido"}), 400


@bp.route("/<product_id>/images", methods=["POST"])
@jwt_required()
def upload_product_image(product_id):
    """
    Adiciona uma imagem ao produto via Cloudinary.
    Requer autenticação.
    Apenas o owner pode adicionar imagens.
    Body (JSON):
        - image: string base64 da imagem (obrigatório)
    """
    user_id = get_jwt_identity()
    data = request.json or {}

    image_data = data.get("image", "").strip()

    if not image_data:
        return jsonify({"error": "image é obrigatório"}), 400

    try:
        product = Product.objects.get(id=product_id)

        # Verifica se usuário é o owner
        if str(product.owner.id) != user_id:
            return jsonify({"error": "apenas o proprietário pode adicionar imagens"}), 403

        # Upload da imagem para o Cloudinary
        upload_result = cloudinary.uploader.upload(
            image_data,
            folder=f"marketplace/products/{product_id}",
            transformation=[
                {"quality": "auto", "fetch_format": "auto"}
            ]
        )

        # Adiciona URL da imagem ao produto
        image_url = upload_result.get("secure_url")
        product.images.append(image_url)
        product.save()

        return jsonify({
            "message": "imagem adicionada com sucesso",
            "image_url": image_url,
            "product": product.to_dict()
        }), 201

    except DoesNotExist:
        return jsonify({"error": "produto não encontrado"}), 404
    except ValidationError:
        return jsonify({"error": "ID inválido"}), 400
    except Exception as e:
        return jsonify({"error": f"erro ao fazer upload da imagem: {str(e)}"}), 500


@bp.route("/<product_id>/generate-code", methods=["POST"])
@jwt_required()
def generate_confirmation_code(product_id):
    """
    Owner gera código de confirmação para a venda.
    Requer autenticação.
    Apenas o owner pode gerar o código.
    """
    user_id = get_jwt_identity()

    try:
        product = Product.objects.get(id=product_id)

        # Verifica se usuário é o owner
        if str(product.owner.id) != user_id:
            return jsonify({"error": "apenas o proprietário pode gerar o código"}), 403

        # Verifica se produto já tem código gerado
        if product.confirmation_code:
            return jsonify({
                "message": "código já existe",
                "confirmation_code": product.confirmation_code
            }), 200

        # Gera código único de 8 caracteres
        while True:
            code = secrets.token_urlsafe(6)[:8].upper()
            # Verifica se código já existe
            if not Product.objects(confirmation_code=code).first():
                break

        # Salva código (existência do código = owner confirmou)
        product.confirmation_code = code
        product.save()

        return jsonify({
            "message": "código gerado com sucesso. Envie este código para o comprador pelo WhatsApp!",
            "confirmation_code": code,
            "product": product.to_dict()
        }), 201

    except DoesNotExist:
        return jsonify({"error": "produto não encontrado"}), 404
    except ValidationError:
        return jsonify({"error": "ID inválido"}), 400


@bp.route("/confirm-with-code", methods=["POST"])
@jwt_required()
def confirm_with_code():
    """
    Buyer usa código de confirmação para confirmar a compra.
    Requer autenticação.
    Body (JSON):
        - confirmation_code: string (obrigatório)
    """
    user_id = get_jwt_identity()
    data = request.json or {}
    code = data.get("confirmation_code", "").strip().upper()

    if not code:
        return jsonify({"error": "confirmation_code é obrigatório"}), 400

    try:
        # Busca produto pelo código
        product = Product.objects.get(confirmation_code=code)

        # Verifica se usuário é o owner (owner não pode confirmar como buyer)
        if str(product.owner.id) == user_id:
            return jsonify({"error": "você não pode confirmar a compra do seu próprio produto"}), 400

        # Verifica se já tem buyer e se é diferente do atual
        if product.buyer and str(product.buyer.id) != user_id:
            return jsonify({"error": "este produto já foi confirmado por outro comprador"}), 400

        # Busca o buyer
        buyer = User.objects.get(id=user_id)

        # Atualiza produto com buyer (definir buyer = confirmar compra)
        product.buyer = buyer
        product.save()

        return jsonify({
            "message": "compra confirmada com sucesso!",
            "product": product.to_dict()
        }), 200

    except DoesNotExist:
        return jsonify({"error": "código inválido"}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400