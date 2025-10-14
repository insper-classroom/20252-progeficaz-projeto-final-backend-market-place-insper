import pytest
from unittest.mock import MagicMock, patch
from app import app, conectar_bd  # Importamos a aplicação Flask e a função de conexão

@pytest.fixture
def client():
    """Cria um cliente de teste para a API."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("app.conectar_bd")
def test_get_products(mock_conectar_bd, client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        (0, "Notebook", "Notebook Alienware muito bom", 100000.00, "Usado", 1, 1, "Anunciado", "2023-10-01 10:00:00"),
        (1, "Iphone 15", "Iphone 15 pro max muito bom", 2000.00, "Seminovo", 2, 2, "Pausado", "2023-20-02 20:00:00"),
    ]
    mock_conectar_bd.return_value = mock_conn
    
    response = client.get("/products")
    assert response.status_code == 200
    data = response.get_json() == [
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
            "user_id": 2,
            "status": "Pausado",
            "created_at": "2023-20-02 20:00:00"
        }
    ]

@pytest.mark.parametrize(
    'product_id, mock_result',
    [
    (0, (0, "Notebook", "Notebook Alienware muito bom", 100000.00, "Usado", 1, 1, "Anunciado", "2023-10-01 10:00:00")),
    (1, (1, "Iphone 15", "Iphone 15 pro max muito bom", 2000.00, "Seminovo", 2, 2, "Pausado", "2023-20-02 20:00:00"))
    ]
)


def test_get_product_by_id(client, id, mock_result):
    with patch("app.conectar_bd") as mock_conectar_bd:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = mock_result
        mock_conectar_bd.return_value = mock_conn
        response = client.get(f'/products/{id}')
    
    # THEN
        assert response.status_code == 200
        assert response.get_json() == mock_result

    
