import pytest
from unittest.mock import MagicMock, patch
from app import app  

# cliente teste
@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================== GET ==============================
#  todos os produtos
@patch("app.conectar_bd")
def test_get_items(mock_conectar_bd, client):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    mock_items_collection.find.return_value = [
        {
            "id": 0,
            "name": "Notebook",
            "description": "Notebook Alienware muito bom",
            "price": 100000.00,
            "state": "Usado",
            "category_id": 1,
            "seller_id": 1,
            "status": "Anunciado",
            "created_at": "2023-10-01 10:00:00"
        },
        {
            "id": 1,
            "name": "Iphone 15",
            "description": "Iphone 15 pro max muito bom",
            "price": 2000.00,
            "state": "Seminovo",
            "category_id": 2,
            "seller_id": 2,
            "status": "Pausado",
            "created_at": "2023-02-20 20:00:00"
        }
    ]
    mock_conectar_bd.return_value = mock_db

    response = client.get("/items")
    assert response.status_code == 200
    assert response.get_json() == mock_items_collection.find.return_value


# por id
@patch("app.conectar_bd")
@pytest.mark.parametrize(
    "product_id, mock_doc, expected_json",
    [
        (
            0,
            {
                "id": 0,
                "name": "Notebook",
                "description": "Notebook Alienware muito bom",
                "price": 100000.00,
                "state": "Usado",
                "category_id": 1,
                "seller_id": 1,
                "status": "Anunciado",
                "created_at": "2023-10-01 10:00:00"
            },
            {
                "id": 0,
                "name": "Notebook",
                "description": "Notebook Alienware muito bom",
                "price": 100000.00,
                "state": "Usado",
                "category_id": 1,
                "seller_id": 1,
                "status": "Anunciado",
                "created_at": "2023-10-01 10:00:00"
            },
        ),
        (
            1,
            {
                "id": 1,
                "name": "Iphone 15",
                "description": "Iphone 15 pro max muito bom",
                "price": 2000.00,
                "state": "Seminovo",
                "category_id": 2,
                "seller_id": 2,
                "status": "Pausado",
                "created_at": "2023-02-20 20:00:00"
            },
            {
                "id": 1,
                "name": "Iphone 15",
                "description": "Iphone 15 pro max muito bom",
                "price": 2000.00,
                "state": "Seminovo",
                "category_id": 2,
                "seller_id": 2,
                "status": "Pausado",
                "created_at": "2023-02-20 20:00:00"
            },
        ),
    ],
)
def test_get_product_by_id(mock_conectar_bd, client, product_id, mock_doc, expected_json):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    mock_items_collection.find_one.return_value = mock_doc
    mock_conectar_bd.return_value = mock_db

    response = client.get(f"/items/{product_id}")
    assert response.status_code == 200
    assert response.get_json() == expected_json


# erro produto não encontrado
@patch("app.conectar_bd")
def test_get_product_by_id_not_found(mock_conectar_bd, client):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    mock_items_collection.find_one.return_value = None
    mock_conectar_bd.return_value = mock_db

    response = client.get("/items/999999999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}


# por categoria
@patch("app.conectar_bd")
def test_get_items_by_category(mock_conectar_bd, client):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    mock_items_collection.find.return_value = [
        {
            "id": 0,
            "name": "Notebook",
            "description": "Notebook Alienware muito bom",
            "price": 100000.00,
            "state": "Usado",
            "category_id": 1,
            "seller_id": 1,
            "status": "Anunciado",
            "created_at": "2023-10-01 10:00:00"
        }
    ]
    mock_conectar_bd.return_value = mock_db

    response = client.get("/items/category/1")
    assert response.status_code == 200
    assert response.get_json() == mock_items_collection.find.return_value


# por vendedor
@patch("app.conectar_bd")
def test_get_items_by_seller(mock_conectar_bd, client):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    seller_items = [
        {
            "id": 10,
            "name": "Mesa Gamer",
            "description": "Mesa para setup",
            "price": 450.00,
            "state": "Usado",
            "category_id": 5,
            "seller_id": 42,
            "status": "Anunciado",
            "created_at": "2024-01-10 12:00:00"
        }
    ]
    mock_items_collection.find.return_value = seller_items
    mock_conectar_bd.return_value = mock_db

    response = client.get("/items/seller/42")
    assert response.status_code == 200
    assert response.get_json() == seller_items


# ============================== POST ==============================
@patch("app.conectar_bd")
def test_post_product(mock_conectar_bd, client):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    insert_result = MagicMock()
    insert_result.inserted_id = "some-id"
    mock_items_collection.insert_one.return_value = insert_result

    mock_conectar_bd.return_value = mock_db

    new_product = {
        "name": "Tablet",
        "description": "Tablet Samsung Galaxy Tab S7",
        "price": 3000.00,
        "state": "Novo",
        "category_id": 3,
        "seller_id": 3,
        "status": "Anunciado"
    }

    response = client.post("/items", json=new_product)
    assert response.status_code == 201
    assert response.get_json() == {"message": "Produto criado com sucesso"}

    assert mock_items_collection.insert_one.call_count == 1
    called_arg = mock_items_collection.insert_one.call_args[0][0]
    assert called_arg["name"] == new_product["name"]
    assert called_arg["price"] == new_product["price"]


# erro de dados inválidos
def test_post_product_invalid_data(client):
    invalid_product = {
        "name": "",
        "description": "Tablet Samsung Galaxy Tab S7",
        "price": -3000.00,
        "state": "Novo",
        "category_id": 3,
        "seller_id": 3,
        "status": "Anunciado"
    }

    response = client.post("/items", json=invalid_product)
    assert response.status_code == 400
    assert response.get_json() == {"error": "Dados inválidos"}


# ============================== PUT ==============================
@patch("app.conectar_bd")
def test_update_product_success(mock_conectar_bd, client):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    update_result = MagicMock()
    update_result.matched_count = 1
    update_result.modified_count = 1
    mock_items_collection.update_one.return_value = update_result

    mock_conectar_bd.return_value = mock_db

    update_payload = {
        "price": 1999.99,
        "status": "Anunciado"
    }

    response = client.put("/items/1", json=update_payload)
    assert response.status_code == 200
    assert response.get_json() == {"message": "Produto atualizado com sucesso"}

    assert mock_items_collection.update_one.call_count == 1
    called_filter = mock_items_collection.update_one.call_args[0][0]
    assert called_filter.get("id") == 1 or called_filter.get("_id") == 1


# erro produto não encontrado
@patch("app.conectar_bd")
def test_update_product_not_found(mock_conectar_bd, client):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    update_result = MagicMock()
    update_result.matched_count = 0
    update_result.modified_count = 0
    mock_items_collection.update_one.return_value = update_result

    mock_conectar_bd.return_value = mock_db

    update_payload = {"price": 1999.99}
    response = client.put("/items/999999", json=update_payload)
    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}


# ============================== DELETE ==============================
@patch("app.conectar_bd")
def test_delete_product_success(mock_conectar_bd, client):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    delete_result = MagicMock()
    delete_result.deleted_count = 1
    mock_items_collection.delete_one.return_value = delete_result

    mock_conectar_bd.return_value = mock_db

    response = client.delete("/items/1")
    assert response.status_code == 200
    assert response.get_json() == {"message": "Produto removido com sucesso"}
    assert mock_items_collection.delete_one.call_count == 1
    called_filter = mock_items_collection.delete_one.call_args[0][0]
    assert called_filter.get("id") == 1 or called_filter.get("_id") == 1


# erro produto não encontrado
@patch("app.conectar_bd")
def test_delete_product_not_found(mock_conectar_bd, client):
    mock_db = MagicMock()
    mock_items_collection = MagicMock()
    mock_db.items = mock_items_collection

    delete_result = MagicMock()
    delete_result.deleted_count = 0
    mock_items_collection.delete_one.return_value = delete_result

    mock_conectar_bd.return_value = mock_db

    response = client.delete("/items/999999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}
