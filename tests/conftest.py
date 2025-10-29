import pytest
import mongomock
from app import create_app
from app.models import User, Product
from mongoengine import disconnect


@pytest.fixture(scope="function")
def app():
    """
    Cria uma instância da aplicação Flask para testes.
    Usa mongomock para simular o MongoDB.
    """
    disconnect(alias='default')

    test_app = create_app()
    test_app.config.update({
        "TESTING": True,
        "MONGO_URI": "mongomock://localhost/test_db",
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only"
    })

    # Limpa coleções antes do teste
    try:
        User.objects.delete()
    except:
        pass
    try:
        Product.objects.delete()
    except:
        pass

    yield test_app

    # Cleanup após cada teste
    try:
        User.objects.delete()
    except:
        pass
    try:
        Product.objects.delete()
    except:
        pass
    disconnect(alias='default')


@pytest.fixture(scope="function")
def client(app):
    """
    Cliente de teste Flask.
    """
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """
    CLI runner para testes.
    """
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def auth_headers(client):
    """
    Fixture que cria um usuário, faz login e retorna headers com token JWT.
    """
    # Registra usuário
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123",
        "cellphone": "+5511999999999"
    }
    client.post("/auth/register", json=user_data)

    # Faz login
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def second_user_headers(client):
    """
    Fixture que cria um segundo usuário para testes de interação.
    """
    # Registra segundo usuário
    user_data = {
        "email": "buyer@example.com",
        "name": "Buyer User",
        "password": "buyerpass123",
        "cellphone": "+5511988888888"
    }
    client.post("/auth/register", json=user_data)

    # Faz login
    login_data = {
        "email": "buyer@example.com",
        "password": "buyerpass123"
    }
    response = client.post("/auth/login", json=login_data)
    token = response.json["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_product(client, auth_headers):
    """
    Fixture que cria um produto de exemplo.
    """
    product_data = {
        "title": "iPhone 15",
        "description": "Novo na caixa",
        "price": 5000.00
    }
    response = client.post("/products", json=product_data, headers=auth_headers)
    return response.json["product"]
