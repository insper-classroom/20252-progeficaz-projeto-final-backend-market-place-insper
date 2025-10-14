import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from datetime import datetime, timedelta
from bson import ObjectId
##from usuario import login_usuario, auth_required  # Ainda nn temos usuario

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    JWTManager(app)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_db():
    mock = MagicMock()
    return mock

def test_successful_login(app, client, mock_db):
    test_user = {
        "_id": ObjectId(),
        "email": "test@test.com",
        "senha": "password123",
        "nome": "Test User"
    }
    
    with patch('usuario.mongo.db.usuarios', mock_db):
        mock_db.find_one.return_value = test_user
        
        response = client.post('/login', json={
            "email": "test@test.com",
            "senha": "password123"
        })
        
        assert response.status_code == 200
        assert 'access_token' in response.json

def test_failed_login_wrong_password(app, client, mock_db):
    test_user = {
        "_id": ObjectId(),
        "email": "test@test.com",
        "senha": "password123",
        "nome": "Test User"
    }
    
    with patch('usuario.mongo.db.usuarios', mock_db):
        mock_db.find_one.return_value = test_user
        
        response = client.post('/login', json={
            "email": "test@test.com",
            "senha": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert 'message' in response.json

def test_failed_login_user_not_found(app, client, mock_db):
    with patch('usuario.mongo.db.usuarios', mock_db):
        mock_db.find_one.return_value = None
        
        response = client.post('/login', json={
            "email": "nonexistent@test.com",
            "senha": "password123"
        })
        
        assert response.status_code == 404
        assert 'message' in response.json

@patch('flask_jwt_extended.view_decorators.verify_jwt_in_request')
def test_auth_required_valid_token(mock_verify_jwt, app, client):
    with app.test_request_context():
        mock_verify_jwt.return_value = True
        
        @app.route('/protected')
        @auth_required
        def protected_route():
            return jsonify({"message": "Access granted"})
        
        token = create_access_token(identity="test@test.com")
        response = client.get('/protected', 
                            headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200

def test_auth_required_invalid_token(app, client):
    with app.test_request_context():
        @app.route('/protected')
        @auth_required
        def protected_route():
            return jsonify({"message": "Access granted"})
        
        response = client.get('/protected', 
                            headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401

def test_auth_required_no_token(app, client):
    with app.test_request_context():
        @app.route('/protected')
        @auth_required
        def protected_route():
            return jsonify({"message": "Access granted"})
        
        response = client.get('/protected')
        
        assert response.status_code == 401

def test_token_expiration(app, client):
    with app.test_request_context():
        @app.route('/protected')
        @auth_required
        def protected_route():
            return jsonify({"message": "Access granted"})
        
        expired_token = create_access_token(
            identity="test@test.com",
            expires_delta=timedelta(seconds=-1)
        )
        
        response = client.get('/protected', 
                            headers={'Authorization': f'Bearer {expired_token}'})
        
        assert response.status_code == 401