import pytest


class TestListProducts:
    """Testes para a rota de listagem (GET /products)"""

    def test_list_empty_products(self, client):
        """Deve retornar lista vazia quando não há produtos"""
        response = client.get("/products")

        assert response.status_code == 200
        assert response.json == []

    def test_list_products(self, client, auth_headers):
        """Deve listar produtos disponíveis"""
        # Cria alguns produtos
        products = [
            {"title": "Produto 1", "description": "Desc 1", "price": 100.0},
            {"title": "Produto 2", "description": "Desc 2", "price": 200.0},
            {"title": "Produto 3", "description": "Desc 3", "price": 300.0}
        ]
        for p in products:
            client.post("/products", json=p, headers=auth_headers)

        # Lista produtos
        response = client.get("/products")

        assert response.status_code == 200
        assert len(response.json) == 3
        assert all("id" in p for p in response.json)
        assert all("title" in p for p in response.json)
        # Verifica que owner é objeto completo
        assert all("owner" in p for p in response.json)
        assert all(isinstance(p["owner"], dict) for p in response.json)
        assert all("email" in p["owner"] for p in response.json)
        assert all("cellphone" in p["owner"] for p in response.json)

    def test_list_products_excludes_sold(self, client, auth_headers, second_user_headers):
        """Deve excluir produtos já vendidos da listagem"""
        # Cria produto
        product_data = {"title": "iPhone", "description": "Novo", "price": 5000.0}
        response = client.post("/products", json=product_data, headers=auth_headers)
        product_id = response.json["product"]["id"]

        # Verifica que aparece na listagem
        response = client.get("/products")
        assert len(response.json) == 1

        # Owner gera código e buyer confirma
        gen_response = client.post(f"/products/{product_id}/generate-code", headers=auth_headers)
        code = gen_response.json["confirmation_code"]
        client.post("/products/confirm-with-code",
                   json={"confirmation_code": code},
                   headers=second_user_headers)

        # Verifica que não aparece mais na listagem
        response = client.get("/products")
        assert len(response.json) == 0

    def test_search_products_by_title(self, client, auth_headers):
        """Deve buscar produtos por título"""
        # Cria produtos
        products = [
            {"title": "iPhone 15", "description": "Smartphone Apple", "price": 5000.0},
            {"title": "Samsung Galaxy", "description": "Smartphone Samsung", "price": 3000.0},
            {"title": "iPad Pro", "description": "Tablet Apple", "price": 7000.0}
        ]
        for p in products:
            client.post("/products", json=p, headers=auth_headers)

        # Busca por "iPhone"
        response = client.get("/products?q=iPhone")
        assert response.status_code == 200
        assert len(response.json) == 1
        assert "iPhone" in response.json[0]["title"]

    def test_search_products_by_description(self, client, auth_headers):
        """Deve buscar produtos por descrição"""
        # Cria produtos
        products = [
            {"title": "iPhone 15", "description": "Smartphone Apple", "price": 5000.0},
            {"title": "Samsung Galaxy", "description": "Smartphone Samsung", "price": 3000.0},
            {"title": "iPad Pro", "description": "Tablet Apple", "price": 7000.0}
        ]
        for p in products:
            client.post("/products", json=p, headers=auth_headers)

        # Busca por "Tablet"
        response = client.get("/products?q=Tablet")
        assert response.status_code == 200
        assert len(response.json) == 1
        assert "Tablet" in response.json[0]["description"]

    def test_search_products_case_insensitive(self, client, auth_headers):
        """Busca deve ser case insensitive"""
        product_data = {"title": "iPhone 15", "description": "Novo", "price": 5000.0}
        client.post("/products", json=product_data, headers=auth_headers)

        # Busca com minúsculas
        response = client.get("/products?q=iphone")
        assert response.status_code == 200
        assert len(response.json) == 1


class TestCreateProduct:
    """Testes para a rota de criação (POST /products)"""

    def test_create_product_success(self, client, auth_headers):
        """Deve criar produto com sucesso"""
        product_data = {
            "title": "MacBook Pro",
            "description": "Laptop Apple M3",
            "price": 15000.0
        }
        response = client.post("/products", json=product_data, headers=auth_headers)

        assert response.status_code == 201
        assert "product" in response.json
        assert response.json["product"]["title"] == "MacBook Pro"
        assert response.json["product"]["description"] == "Laptop Apple M3"
        assert response.json["product"]["price"] == 15000.0
        assert "owner" in response.json["product"]
        assert isinstance(response.json["product"]["owner"], dict)
        assert "email" in response.json["product"]["owner"]
        assert "cellphone" in response.json["product"]["owner"]
        assert response.json["product"]["buyer"] is None

    def test_create_product_without_auth(self, client):
        """Deve retornar erro 401 sem autenticação"""
        product_data = {
            "title": "Produto Teste",
            "description": "Descrição",
            "price": 100.0
        }
        response = client.post("/products", json=product_data)

        assert response.status_code == 401

    def test_create_product_without_title(self, client, auth_headers):
        """Deve retornar erro 400 sem título"""
        product_data = {
            "description": "Sem título",
            "price": 100.0
        }
        response = client.post("/products", json=product_data, headers=auth_headers)

        assert response.status_code == 400
        assert "error" in response.json

    def test_create_product_without_price(self, client, auth_headers):
        """Deve retornar erro 400 sem preço"""
        product_data = {
            "title": "Produto Sem Preço",
            "description": "Teste"
        }
        response = client.post("/products", json=product_data, headers=auth_headers)

        assert response.status_code == 400
        assert "error" in response.json

    def test_create_product_with_negative_price(self, client, auth_headers):
        """Deve retornar erro 400 com preço negativo"""
        product_data = {
            "title": "Produto Preço Negativo",
            "description": "Teste",
            "price": -100.0
        }
        response = client.post("/products", json=product_data, headers=auth_headers)

        assert response.status_code == 400
        assert "error" in response.json

    def test_create_product_with_zero_price(self, client, auth_headers):
        """Deve permitir criar produto com preço zero"""
        product_data = {
            "title": "Produto Grátis",
            "description": "De graça",
            "price": 0.0
        }
        response = client.post("/products", json=product_data, headers=auth_headers)

        assert response.status_code == 201
        assert response.json["product"]["price"] == 0.0

    def test_create_product_with_invalid_price(self, client, auth_headers):
        """Deve retornar erro 400 com preço inválido"""
        product_data = {
            "title": "Produto Preço Inválido",
            "description": "Teste",
            "price": "não é número"
        }
        response = client.post("/products", json=product_data, headers=auth_headers)

        assert response.status_code == 400
        assert "error" in response.json

    def test_create_product_without_description(self, client, auth_headers):
        """Deve permitir criar produto sem descrição"""
        product_data = {
            "title": "Produto Sem Descrição",
            "price": 250.0
        }
        response = client.post("/products", json=product_data, headers=auth_headers)

        assert response.status_code == 201
        assert response.json["product"]["description"] == ""


class TestGetProduct:
    """Testes para a rota de detalhes (GET /products/<product_id>)"""

    def test_get_product_success(self, client, sample_product):
        """Deve retornar detalhes do produto"""
        product_id = sample_product["id"]
        response = client.get(f"/products/{product_id}")

        assert response.status_code == 200
        assert response.json["id"] == product_id
        assert response.json["title"] == sample_product["title"]
        assert response.json["price"] == sample_product["price"]
        # Verifica que owner é objeto completo
        assert "owner" in response.json
        assert isinstance(response.json["owner"], dict)
        assert "email" in response.json["owner"]
        assert "cellphone" in response.json["owner"]
        assert response.json["owner"]["email"] == "test@example.com"

    def test_get_product_not_found(self, client):
        """Deve retornar erro 404 para produto inexistente"""
        fake_id = "507f1f77bcf86cd799439011"  # ID MongoDB válido mas inexistente
        response = client.get(f"/products/{fake_id}")

        assert response.status_code == 404
        assert "error" in response.json

    def test_get_product_invalid_id(self, client):
        """Deve retornar erro 400 para ID inválido"""
        invalid_id = "invalid_id_format"
        response = client.get(f"/products/{invalid_id}")

        assert response.status_code == 400
        assert "error" in response.json


class TestGenerateCode:
    """Testes para a rota de geração de código (POST /products/<product_id>/generate-code)"""

    def test_generate_code_success(self, client, auth_headers, sample_product):
        """Deve gerar código com sucesso"""
        product_id = sample_product["id"]

        response = client.post(f"/products/{product_id}/generate-code", headers=auth_headers)

        assert response.status_code == 201
        assert "confirmation_code" in response.json
        assert len(response.json["confirmation_code"]) == 8
        assert "message" in response.json

    def test_generate_code_already_exists(self, client, auth_headers, sample_product):
        """Deve retornar código existente se já foi gerado"""
        product_id = sample_product["id"]

        # Primeira geração
        response1 = client.post(f"/products/{product_id}/generate-code", headers=auth_headers)
        code1 = response1.json["confirmation_code"]

        # Segunda tentativa
        response2 = client.post(f"/products/{product_id}/generate-code", headers=auth_headers)
        code2 = response2.json["confirmation_code"]

        assert response2.status_code == 200
        assert code1 == code2

    def test_generate_code_not_owner(self, client, second_user_headers, sample_product):
        """Deve retornar erro 403 se não for o owner"""
        product_id = sample_product["id"]

        response = client.post(f"/products/{product_id}/generate-code", headers=second_user_headers)

        assert response.status_code == 403
        assert "error" in response.json

    def test_generate_code_without_auth(self, client, sample_product):
        """Deve retornar erro 401 sem autenticação"""
        product_id = sample_product["id"]

        response = client.post(f"/products/{product_id}/generate-code")

        assert response.status_code == 401

    def test_generate_code_nonexistent_product(self, client, auth_headers):
        """Deve retornar erro 404 para produto inexistente"""
        fake_id = "507f1f77bcf86cd799439011"

        response = client.post(f"/products/{fake_id}/generate-code", headers=auth_headers)

        assert response.status_code == 404


class TestConfirmWithCode:
    """Testes para a rota de confirmação com código (POST /products/confirm-with-code)"""

    def test_confirm_with_code_success(self, client, auth_headers, second_user_headers, sample_product):
        """Deve confirmar compra com código válido"""
        product_id = sample_product["id"]

        # Owner gera código
        gen_response = client.post(f"/products/{product_id}/generate-code", headers=auth_headers)
        code = gen_response.json["confirmation_code"]

        # Buyer confirma com código
        response = client.post("/products/confirm-with-code",
                              json={"confirmation_code": code},
                              headers=second_user_headers)

        assert response.status_code == 200
        assert "message" in response.json
        assert response.json["product"]["buyer"] is not None
        assert isinstance(response.json["product"]["buyer"], dict)
        assert "email" in response.json["product"]["buyer"]
        assert "cellphone" in response.json["product"]["buyer"]
        assert response.json["product"]["buyer"]["email"] == "buyer@example.com"

    def test_confirm_with_code_invalid_code(self, client, second_user_headers):
        """Deve retornar erro 404 com código inválido"""
        response = client.post("/products/confirm-with-code",
                              json={"confirmation_code": "INVALID1"},
                              headers=second_user_headers)

        assert response.status_code == 404
        assert "error" in response.json

    def test_confirm_with_code_owner_cannot_confirm(self, client, auth_headers, sample_product):
        """Owner não pode confirmar compra do próprio produto"""
        product_id = sample_product["id"]

        # Owner gera código
        gen_response = client.post(f"/products/{product_id}/generate-code", headers=auth_headers)
        code = gen_response.json["confirmation_code"]

        # Owner tenta confirmar (deve falhar)
        response = client.post("/products/confirm-with-code",
                              json={"confirmation_code": code},
                              headers=auth_headers)

        assert response.status_code == 400
        assert "error" in response.json
        assert "próprio produto" in response.json["error"].lower()

    def test_confirm_with_code_already_confirmed(self, client, auth_headers, second_user_headers, sample_product):
        """Não deve permitir outro buyer confirmar produto já confirmado"""
        product_id = sample_product["id"]

        # Owner gera código
        gen_response = client.post(f"/products/{product_id}/generate-code", headers=auth_headers)
        code = gen_response.json["confirmation_code"]

        # Primeiro buyer confirma
        client.post("/products/confirm-with-code",
                   json={"confirmation_code": code},
                   headers=second_user_headers)

        # Cria terceiro usuário
        third_user_data = {
            "email": "third@example.com",
            "name": "Third User",
            "password": "thirdpass123",
            "cellphone": "+5511977777777"
        }
        client.post("/auth/register", json=third_user_data)
        login_response = client.post("/auth/login", json={
            "email": "third@example.com",
            "password": "thirdpass123"
        })
        third_user_headers = {"Authorization": f"Bearer {login_response.json['access_token']}"}

        # Terceiro usuário tenta confirmar (deve falhar)
        response = client.post("/products/confirm-with-code",
                              json={"confirmation_code": code},
                              headers=third_user_headers)

        assert response.status_code == 400
        assert "error" in response.json

    def test_confirm_with_code_without_code(self, client, second_user_headers):
        """Deve retornar erro 400 sem código"""
        response = client.post("/products/confirm-with-code",
                              json={},
                              headers=second_user_headers)

        assert response.status_code == 400
        assert "error" in response.json

    def test_confirm_with_code_without_auth(self, client):
        """Deve retornar erro 401 sem autenticação"""
        response = client.post("/products/confirm-with-code",
                              json={"confirmation_code": "TESTCODE"})

        assert response.status_code == 401


class TestListProductsWithConfirmation:
    """Testes para verificar que produtos confirmados não aparecem na listagem"""

    def test_list_excludes_products_with_buyer(self, client, auth_headers, second_user_headers, sample_product):
        """Produtos com buyer devem ser excluídos da listagem"""
        product_id = sample_product["id"]

        # Verifica que aparece na listagem
        response = client.get("/products")
        assert len(response.json) == 1

        # Owner gera código e buyer confirma
        gen_response = client.post(f"/products/{product_id}/generate-code", headers=auth_headers)
        code = gen_response.json["confirmation_code"]
        client.post("/products/confirm-with-code",
                   json={"confirmation_code": code},
                   headers=second_user_headers)

        # Verifica que não aparece mais na listagem
        response = client.get("/products")
        assert len(response.json) == 0


class TestUploadProductImages:
    """Testes para a rota de upload de imagens (POST /products/<product_id>/images)"""

    def test_upload_image_returns_images_and_thumbnail_fields(self, client, auth_headers, sample_product):
        """Deve retornar campos images e thumbnail em todos os endpoints"""
        product_id = sample_product["id"]

        # Verifica que produto sem imagens tem campos vazios
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 200
        assert "images" in response.json
        assert "thumbnail" in response.json
        assert response.json["images"] == []
        assert response.json["thumbnail"] is None

    def test_product_creation_includes_empty_images(self, client, auth_headers):
        """Produto recém-criado deve ter images=[] e thumbnail=null"""
        product_data = {
            "title": "Produto Teste",
            "description": "Teste",
            "price": 100.0
        }
        response = client.post("/products", json=product_data, headers=auth_headers)

        assert response.status_code == 201
        assert "images" in response.json["product"]
        assert "thumbnail" in response.json["product"]
        assert response.json["product"]["images"] == []
        assert response.json["product"]["thumbnail"] is None

    def test_list_products_includes_images_and_thumbnail(self, client, auth_headers):
        """Listagem de produtos deve incluir campos images e thumbnail"""
        product_data = {"title": "Produto", "description": "Desc", "price": 100.0}
        client.post("/products", json=product_data, headers=auth_headers)

        response = client.get("/products")
        assert response.status_code == 200
        assert len(response.json) > 0
        for product in response.json:
            assert "images" in product
            assert "thumbnail" in product
