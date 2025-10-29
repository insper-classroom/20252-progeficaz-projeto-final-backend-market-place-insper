import pytest


class TestRegister:
    """Testes para a rota de registro (POST /auth/register)"""

    def test_register_success(self, client):
        """Deve registrar um novo usuário com sucesso"""
        data = {
            "email": "newuser@example.com",
            "name": "New User",
            "password": "securepass123",
            "cellphone": "+5511999999999"
        }
        response = client.post("/auth/register", json=data)

        assert response.status_code == 201
        assert "user" in response.json
        assert response.json["user"]["email"] == "newuser@example.com"
        assert response.json["user"]["name"] == "New User"
        assert response.json["user"]["cellphone"] == "+5511999999999"
        assert "id" in response.json["user"]
        assert "password" not in response.json["user"]

    def test_register_without_email(self, client):
        """Deve retornar erro 400 se email não for fornecido"""
        data = {
            "name": "User Without Email",
            "password": "password123",
            "cellphone": "+5511999999999"
        }
        response = client.post("/auth/register", json=data)

        assert response.status_code == 400
        assert "error" in response.json

    def test_register_without_password(self, client):
        """Deve retornar erro 400 se password não for fornecido"""
        data = {
            "email": "nopassword@example.com",
            "name": "No Password User",
            "cellphone": "+5511999999999"
        }
        response = client.post("/auth/register", json=data)

        assert response.status_code == 400
        assert "error" in response.json

    def test_register_without_cellphone(self, client):
        """Deve retornar erro 400 se cellphone não for fornecido"""
        data = {
            "email": "nocellphone@example.com",
            "name": "No Cellphone User",
            "password": "password123"
        }
        response = client.post("/auth/register", json=data)

        assert response.status_code == 400
        assert "error" in response.json

    def test_register_duplicate_email(self, client):
        """Deve retornar erro 409 ao tentar registrar email duplicado"""
        data = {
            "email": "duplicate@example.com",
            "name": "First User",
            "password": "password123",
            "cellphone": "+5511999999999"
        }
        # Primeiro registro
        response1 = client.post("/auth/register", json=data)
        assert response1.status_code == 201

        # Segundo registro com mesmo email
        data["name"] = "Second User"
        data["cellphone"] = "+5511988888888"
        response2 = client.post("/auth/register", json=data)
        assert response2.status_code == 409
        assert "error" in response2.json

    def test_register_invalid_email(self, client):
        """Deve retornar erro ao tentar registrar com email inválido"""
        data = {
            "email": "not-an-email",
            "name": "Invalid Email User",
            "password": "password123",
            "cellphone": "+5511999999999"
        }
        response = client.post("/auth/register", json=data)

        assert response.status_code == 400


class TestLogin:
    """Testes para a rota de login (POST /auth/login)"""

    def test_login_success(self, client):
        """Deve fazer login com credenciais válidas"""
        # Primeiro registra usuário
        register_data = {
            "email": "logintest@example.com",
            "name": "Login Test",
            "password": "mypassword",
            "cellphone": "+5511999999999"
        }
        client.post("/auth/register", json=register_data)

        # Tenta login
        login_data = {
            "email": "logintest@example.com",
            "password": "mypassword"
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 200
        assert "access_token" in response.json
        assert isinstance(response.json["access_token"], str)
        assert len(response.json["access_token"]) > 0

    def test_login_wrong_password(self, client):
        """Deve retornar erro 401 com senha incorreta"""
        # Registra usuário
        register_data = {
            "email": "wrongpass@example.com",
            "name": "Wrong Pass User",
            "password": "correctpassword",
            "cellphone": "+5511999999999"
        }
        client.post("/auth/register", json=register_data)

        # Tenta login com senha errada
        login_data = {
            "email": "wrongpass@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        assert "error" in response.json

    def test_login_nonexistent_user(self, client):
        """Deve retornar erro 401 para usuário inexistente"""
        login_data = {
            "email": "doesnotexist@example.com",
            "password": "anypassword"
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        assert "error" in response.json

    def test_login_without_email(self, client):
        """Deve retornar erro 400 se email não for fornecido"""
        login_data = {
            "password": "password123"
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 400
        assert "error" in response.json

    def test_login_without_password(self, client):
        """Deve retornar erro 400 se password não for fornecido"""
        login_data = {
            "email": "test@example.com"
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 400
        assert "error" in response.json


class TestMe:
    """Testes para a rota de perfil (GET /auth/me)"""

    def test_me_success(self, client, auth_headers):
        """Deve retornar dados do usuário autenticado"""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        assert "email" in response.json
        assert "name" in response.json
        assert "cellphone" in response.json
        assert "id" in response.json
        assert response.json["email"] == "test@example.com"
        assert response.json["cellphone"] == "+5511999999999"
        assert "password" not in response.json

    def test_me_without_token(self, client):
        """Deve retornar erro 401 sem token de autenticação"""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_me_with_invalid_token(self, client):
        """Deve retornar erro 422 com token inválido"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == 422
