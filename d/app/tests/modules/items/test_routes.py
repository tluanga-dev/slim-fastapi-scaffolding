import pytest
from app.modules.items.schemas import ItemCreate

def test_create_item(test_client):
    response = test_client.post("/items/", json={
        "name": "Test Item",
        "description": "Test Description"
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"

def test_get_item(test_client):
    # Create item first
    create_response = test_client.post("/items/", json={
        "name": "Test Get",
        "description": "Test"
    })
    item_id = create_response.json()["id"]
    
    # Get item
    response = test_client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["id"] == item_id

def test_get_nonexistent_item(test_client):
    response = test_client.get("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"