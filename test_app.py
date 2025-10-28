from io import BytesIO
import pytest
from unittest.mock import MagicMock, patch
from bson.objectid import ObjectId

# ============================== FIXTURES ==============================
@pytest.fixture
def client():
    """Cria cliente de teste com app context"""
    with patch('app.connect_db'):  # Mock da conexão do BD
        from app import create_app
        app = create_app()
        app.config["TESTING"] = True
        
        # Mock do db no app
        mock_db = MagicMock()
        app.db = mock_db
        
        with app.test_client() as client:
            yield client


# ============================== GET TESTS ==============================
@patch("routes.items.get_collection")
def test_get_items(mock_get_collection, client):
    """Testa listagem de todos os itens"""
    mock_collection = MagicMock()
    mock_items = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "title": "Notebook Alienware",
            "description": "Notebook muito bom",
            "price": 5000.00,
            "condition": "Usado",
            "category": "Eletrônicos",
            "seller_id": "user123",
            "status": "Ativo"
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "title": "iPhone 15",
            "description": "iPhone novo",
            "price": 4000.00,
            "condition": "Novo",
            "category": "Eletrônicos",
            "seller_id": "user456",
            "status": "Ativo"
        }
    ]
    
    mock_collection.find.return_value = mock_items
    mock_get_collection.return_value = mock_collection

    response = client.get("/items")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["title"] == "Notebook Alienware"
    assert data[0]["_id"] == "507f1f77bcf86cd799439011"


@patch("routes.items.get_collection")
def test_get_item_by_id(mock_get_collection, client):
    """Testa busca de item por ID"""
    mock_collection = MagicMock()
    item_id = "507f1f77bcf86cd799439011"
    mock_item = {
        "_id": ObjectId(item_id),
        "title": "Notebook Alienware",
        "description": "Notebook muito bom",
        "price": 5000.00,
        "condition": "Usado",
        "category": "Eletrônicos",
        "seller_id": "user123",
        "status": "Ativo"
    }
    
    mock_collection.find_one.return_value = mock_item
    mock_get_collection.return_value = mock_collection

    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Notebook Alienware"
    assert data["_id"] == item_id


@patch("routes.items.get_collection")
def test_get_item_not_found(mock_get_collection, client):
    """Testa busca de item inexistente"""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    mock_get_collection.return_value = mock_collection

    response = client.get("/items/507f1f77bcf86cd799439999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}


@patch("routes.items.get_collection")
def test_get_item_invalid_id(mock_get_collection, client):
    """Testa busca com ID inválido"""
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection

    response = client.get("/items/invalid_id")
    assert response.status_code == 400
    assert "error" in response.get_json()


@patch("routes.items.get_collection")
def test_get_items_by_category(mock_get_collection, client):
    """Testa busca por categoria"""
    mock_collection = MagicMock()
    mock_items = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "title": "Notebook",
            "category": "Eletrônicos"
        }
    ]
    
    mock_collection.find.return_value = mock_items
    mock_get_collection.return_value = mock_collection

    response = client.get("/items/category/Eletrônicos")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1


@patch("routes.items.get_collection")
def test_get_items_by_seller(mock_get_collection, client):
    """Testa busca por vendedor"""
    mock_collection = MagicMock()
    mock_items = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "title": "Mesa Gamer",
            "seller_id": "user123"
        }
    ]
    
    mock_collection.find.return_value = mock_items
    mock_get_collection.return_value = mock_collection

    response = client.get("/items/seller/user123")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["seller_id"] == "user123"


# ============================== POST TESTS ==============================
@patch("routes.items.get_collection")
def test_create_item(mock_get_collection, client):
    """Testa criação de item"""
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
    mock_collection.insert_one.return_value = mock_result
    mock_get_collection.return_value = mock_collection

    new_item = {
        "title": "Tablet Samsung",
        "description": "Tablet novo",
        "price": 1500.00,
        "condition": "Novo",
        "category": "Eletrônicos",
        "seller_id": "user789",
        "status": "Ativo"
    }

    response = client.post("/items", json=new_item)
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Produto criado com sucesso"
    assert "id" in data
    
    # Verifica se insert_one foi chamado
    assert mock_collection.insert_one.call_count == 1


@patch("routes.items.get_collection")
def test_create_item_invalid_data(mock_get_collection, client):
    """Testa criação com dados inválidos"""
    invalid_items = [
        {"description": "Sem título", "price": 100},  # Sem título
        {"title": "Item", "price": -100},  # Preço negativo
        {"title": "Item", "price": 0},  # Preço zero
        {},  # Vazio
    ]
    
    for invalid_item in invalid_items:
        response = client.post("/items", json=invalid_item)
        assert response.status_code == 400
        assert response.get_json() == {"error": "Dados inválidos"}

@patch("routes.items.get_collection")
def test_create_item_with_image(mock_get_collection, client):
    """Testa criação de item com upload de imagem"""
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
    mock_collection.insert_one.return_value = mock_result
    mock_get_collection.return_value = mock_collection

    # Simula um arquivo de imagem em memória
    fake_image = (BytesIO(b"fake image data"), "produto_teste.jpg")

    data = {
        "title": "Câmera Canon",
        "description": "Excelente qualidade",
        "price": "2999.99",
        "condition": "Novo",
        "category": "Eletrônicos",
    }

    response = client.post(
        "/",  # rota de criação de produto
        data={**data, "image": fake_image},
        content_type="multipart/form-data"
    )

    assert response.status_code == 201
    result = response.get_json()
    assert result["message"] == "Produto criado com sucesso"
    assert "image_url" in result
    assert mock_collection.insert_one.call_count == 1

# ============================== PUT TESTS ==============================
@patch("routes.items.get_collection")
def test_update_item(mock_get_collection, client):
    """Testa atualização de item"""
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.matched_count = 1
    mock_result.modified_count = 1
    mock_collection.update_one.return_value = mock_result
    mock_get_collection.return_value = mock_collection

    update_data = {
        "price": 4500.00,
        "status": "Vendido"
    }

    response = client.put("/items/507f1f77bcf86cd799439011", json=update_data)
    assert response.status_code == 200
    assert response.get_json() == {"message": "Produto atualizado com sucesso"}
    
    # Verifica se update_one foi chamado
    assert mock_collection.update_one.call_count == 1


@patch("routes.items.get_collection")
def test_update_item_not_found(mock_get_collection, client):
    """Testa atualização de item inexistente"""
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.matched_count = 0
    mock_collection.update_one.return_value = mock_result
    mock_get_collection.return_value = mock_collection

    update_data = {"price": 4500.00}
    response = client.put("/items/507f1f77bcf86cd799439999", json=update_data)
    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}


# ============================== DELETE TESTS ==============================
@patch("routes.items.get_collection")
def test_delete_item(mock_get_collection, client):
    """Testa remoção de item"""
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_result
    mock_get_collection.return_value = mock_collection

    response = client.delete("/items/507f1f77bcf86cd799439011")
    assert response.status_code == 200
    assert response.get_json() == {"message": "Produto removido com sucesso"}
    
    # Verifica se delete_one foi chamado
    assert mock_collection.delete_one.call_count == 1


@patch("routes.items.get_collection")
def test_delete_item_not_found(mock_get_collection, client):
    """Testa remoção de item inexistente"""
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.deleted_count = 0
    mock_collection.delete_one.return_value = mock_result
    mock_get_collection.return_value = mock_collection

    response = client.delete("/items/507f1f77bcf86cd799439999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}
    
    
    
    
#TODO ARRUMAR TESTES DE ACORDO COM A MUDANÇA NO CÓDIGO