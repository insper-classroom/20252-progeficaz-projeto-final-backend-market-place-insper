import pytest
from unittest.mock import MagicMock, patch
from bson.objectid import ObjectId
import jwt
import os
from datetime import datetime, timedelta

# ============================== FIXTURES ==============================
@pytest.fixture
def client():
    """Cria cliente de teste"""
    with patch('app.connect_db'):
        from app import create_app
        app = create_app()
        app.config["TESTING"] = True
        
        mock_db = MagicMock()
        app.db = mock_db
        
        with app.test_client() as client:
            yield client


@pytest.fixture
def mock_user():
    """Usuário mockado para testes"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "email": "test@al.insper.edu.br",
        "name": "Test User",
        "password": "hashed_password",
        "is_active": True
    }


# ============================== REGISTRO ==============================
@patch("routes.auth.get_collection")
@patch("routes.auth.generate_password_hash")
def test_register_success(mock_hash, mock_get_collection, client):
    """Testa registro de novo usuário"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
    mock_collection.insert_one.return_value = mock_result
    mock_get_collection.return_value = mock_collection
    mock_hash.return_value = "hashed_password"
    
    new_user = {
        "email": "novo@al.insper.edu.br",
        "password": "senha123",
        "name": "Novo User"
    }
    
    response = client.post("/register", json=new_user)
    assert response.status_code == 201
    data = response.get_json()
    assert "token" in data
    assert data["user"]["email"] == new_user["email"]


@patch("routes.auth.get_collection")
def test_register_duplicate_email(mock_get_collection, client):
    """Testa registro com email duplicado"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = {"email": "existe@al.insper.edu.br"}
    mock_get_collection.return_value = mock_collection
    
    new_user = {
        "email": "existe@al.insper.edu.br",
        "password": "senha123",
        "name": "User"
    }
    
    response = client.post("/register", json=new_user)
    assert response.status_code == 409
    assert response.get_json()["error"] == "Email já cadastrado"


@patch("routes.auth.get_collection")
def test_register_invalid_data(mock_get_collection, client):
    """Testa registro com dados inválidos"""
    test_cases = [
        ({"password": "senha123", "name": "User"}, 400),  # Sem email
        ({"email": "test@al.insper.edu.br", "name": "User"}, 400),  # Sem password
        ({"email": "test@al.insper.edu.br", "password": "12345", "name": "User"}, 400),  # Senha curta
        ({"email": "test@gmail.com", "password": "senha123", "name": "User"}, 400),  # Email não-Insper
    ]
    
    for user_data, expected_code in test_cases:
        response = client.post("/register", json=user_data)
        assert response.status_code == expected_code


# ============================== LOGIN ==============================
@patch("routes.auth.get_collection")
@patch("routes.auth.check_password_hash")
def test_login_success(mock_check, mock_get_collection, client, mock_user):
    """Testa login com credenciais válidas"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = mock_user
    mock_get_collection.return_value = mock_collection
    mock_check.return_value = True
    
    credentials = {
        "email": "test@al.insper.edu.br",
        "password": "senha123"
    }
    
    response = client.post("/login", json=credentials)
    assert response.status_code == 200
    data = response.get_json()
    assert "token" in data
    assert data["user"]["email"] == mock_user["email"]


@patch("routes.auth.get_collection")
def test_login_wrong_password(mock_get_collection, client, mock_user):
    """Testa login com senha incorreta"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = mock_user
    mock_get_collection.return_value = mock_collection
    
    with patch("routes.auth.check_password_hash", return_value=False):
        credentials = {
            "email": "test@al.insper.edu.br",
            "password": "senha_errada"
        }
        
        response = client.post("/login", json=credentials)
        assert response.status_code == 401


@patch("routes.auth.get_collection")
def test_login_user_not_found(mock_get_collection, client):
    """Testa login com usuário inexistente"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    mock_get_collection.return_value = mock_collection
    
    credentials = {
        "email": "naoexiste@al.insper.edu.br",
        "password": "senha123"
    }
    
    response = client.post("/login", json=credentials)
    assert response.status_code == 401


# ============================== PERFIL ==============================
@patch("routes.auth.get_collection")
def test_get_profile(mock_get_collection, client, mock_user):
    """Testa busca de perfil com token válido"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = mock_user
    mock_get_collection.return_value = mock_collection
    
    token = jwt.encode({
        'user_id': str(mock_user["_id"]),
        'exp': datetime.now() + timedelta(days=1)
    }, os.getenv("SECRET_KEY", "dev-secret-key"), algorithm="HS256")
    
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["email"] == mock_user["email"]
    assert "password" not in data


def test_get_profile_no_token(client):
    """Testa busca de perfil sem token"""
    response = client.get("/me")
    assert response.status_code == 401
    assert "message" in response.get_json()


def test_get_profile_invalid_token(client):
    """Testa busca de perfil com token inválido"""
    response = client.get("/me", headers={"Authorization": "Bearer token_invalido"})
    assert response.status_code == 401


# ============================== ATUALIZAR PERFIL ==============================
@patch("routes.auth.get_collection")
def test_update_profile(mock_get_collection, client, mock_user):
    """Testa atualização de perfil"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = mock_user
    mock_collection.update_one.return_value = MagicMock()
    mock_get_collection.return_value = mock_collection
    
    token = jwt.encode({
        'user_id': str(mock_user["_id"]),
        'exp': datetime.now() + timedelta(days=1)
    }, os.getenv("SECRET_KEY", "dev-secret-key"), algorithm="HS256")
    
    update_data = {"name": "Nome Atualizado"}
    
    response = client.put(
        "/me",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


# ============================== ALTERAR SENHA ==============================
@patch("routes.auth.get_collection")
@patch("routes.auth.check_password_hash")
@patch("routes.auth.generate_password_hash")
def test_change_password(mock_hash, mock_check, mock_get_collection, client, mock_user):
    """Testa alteração de senha"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = mock_user
    mock_collection.update_one.return_value = MagicMock()
    mock_get_collection.return_value = mock_collection
    mock_check.return_value = True
    mock_hash.return_value = "new_hashed_password"
    
    token = jwt.encode({
        'user_id': str(mock_user["_id"]),
        'exp': datetime.now() + timedelta(days=1)
    }, os.getenv("SECRET_KEY", "dev-secret-key"), algorithm="HS256")
    
    password_data = {
        "old_password": "senha123",
        "new_password": "novasenha123"
    }
    
    response = client.put(
        "/change-password",
        json=password_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


# ============================== VALIDAÇÃO EMAIL INSPER ==============================
@patch("routes.auth.get_collection")
def test_register_non_insper_email(mock_get_collection, client):
    """Testa que apenas emails @al.insper.edu.br são aceitos"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    mock_get_collection.return_value = mock_collection
    
    invalid_emails = [
        "test@gmail.com",
        "test@insper.edu.br",
        "test@al.insper.com",
        "test@outlook.com"
    ]
    
    for email in invalid_emails:
        new_user = {
            "email": email,
            "password": "senha123",
            "name": "Test User"
        }
        
        response = client.post("/register", json=new_user)
        assert response.status_code == 400
        assert response.get_json()["error"] == "E-mail deve ser do Insper"


@patch("routes.auth.get_collection")
@patch("routes.auth.generate_password_hash")
def test_register_valid_insper_email(mock_hash, mock_get_collection, client):
    """Testa que emails @al.insper.edu.br válidos são aceitos"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
    mock_collection.insert_one.return_value = mock_result
    mock_get_collection.return_value = mock_collection
    mock_hash.return_value = "hashed"
    
    valid_emails = [
        "joaos@al.insper.edu.br",
        "maria.silva@al.insper.edu.br",
        "pedro123@al.insper.edu.br"
    ]
    
    for email in valid_emails:
        new_user = {
            "email": email,
            "password": "senha123",
            "name": "Test User"
        }
        
        response = client.post("/register", json=new_user)
        assert response.status_code == 201
        assert "token" in response.get_json()