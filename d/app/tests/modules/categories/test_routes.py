import pytest
from uuid import uuid4
from app.modules.categories.schemas import CategoryCreate

def test_create_root_category(test_client):
    """Test creating a root category."""
    response = test_client.post("/categories/", json={
        "category_name": "Electronics",
        "display_order": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["category_name"] == "Electronics"
    assert data["category_level"] == 1
    assert data["parent_category_id"] is None
    assert data["category_path"] == "Electronics"
    assert data["is_leaf"] == True


def test_create_child_category(test_client):
    """Test creating a child category."""
    # Create parent first
    parent_response = test_client.post("/categories/", json={
        "category_name": "Electronics",
        "display_order": 1
    })
    parent_id = parent_response.json()["id"]
    
    # Create child
    response = test_client.post("/categories/", json={
        "category_name": "Computers",
        "parent_category_id": parent_id,
        "display_order": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["category_name"] == "Computers"
    assert data["category_level"] == 2
    assert data["parent_category_id"] == parent_id
    assert data["category_path"] == "Electronics/Computers"
    assert data["is_leaf"] == True
    
    # Check parent is no longer leaf
    parent_check = test_client.get(f"/categories/{parent_id}")
    assert parent_check.json()["is_leaf"] == False


def test_create_duplicate_category(test_client):
    """Test creating duplicate category under same parent."""
    # Create first category
    test_client.post("/categories/", json={
        "category_name": "Electronics",
        "display_order": 1
    })
    
    # Try to create duplicate
    response = test_client.post("/categories/", json={
        "category_name": "Electronics",
        "display_order": 2
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_category(test_client):
    """Test getting a specific category."""
    # Create category
    create_response = test_client.post("/categories/", json={
        "category_name": "Books",
        "display_order": 2
    })
    category_id = create_response.json()["id"]
    
    # Get category
    response = test_client.get(f"/categories/{category_id}")
    assert response.status_code == 200
    assert response.json()["id"] == category_id
    assert response.json()["category_name"] == "Books"


def test_get_nonexistent_category(test_client):
    """Test getting a category that doesn't exist."""
    fake_id = str(uuid4())
    response = test_client.get(f"/categories/{fake_id}")
    assert response.status_code == 404


def test_get_root_categories(test_client):
    """Test getting all root categories."""
    # Create multiple root categories
    test_client.post("/categories/", json={"category_name": "Electronics", "display_order": 1})
    test_client.post("/categories/", json={"category_name": "Books", "display_order": 2})
    test_client.post("/categories/", json={"category_name": "Clothing", "display_order": 3})
    
    # Get root categories
    response = test_client.get("/categories/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    names = [cat["category_name"] for cat in data]
    assert "Electronics" in names
    assert "Books" in names
    assert "Clothing" in names


def test_get_category_children(test_client):
    """Test getting children of a category."""
    # Create parent
    parent_response = test_client.post("/categories/", json={
        "category_name": "Electronics"
    })
    parent_id = parent_response.json()["id"]
    
    # Create children
    test_client.post("/categories/", json={
        "category_name": "Computers",
        "parent_category_id": parent_id,
        "display_order": 1
    })
    test_client.post("/categories/", json={
        "category_name": "Phones",
        "parent_category_id": parent_id,
        "display_order": 2
    })
    
    # Get children
    response = test_client.get(f"/categories/{parent_id}/children")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [cat["category_name"] for cat in data]
    assert "Computers" in names
    assert "Phones" in names


def test_update_category(test_client):
    """Test updating a category."""
    # Create category
    create_response = test_client.post("/categories/", json={
        "category_name": "Eletronics",  # Typo
        "display_order": 1
    })
    category_id = create_response.json()["id"]
    
    # Update category
    response = test_client.put(f"/categories/{category_id}", json={
        "category_name": "Electronics",  # Fixed typo
        "display_order": 2
    })
    assert response.status_code == 200
    data = response.json()
    assert data["category_name"] == "Electronics"
    assert data["display_order"] == 2


def test_delete_category(test_client):
    """Test deleting a category."""
    # Create category
    create_response = test_client.post("/categories/", json={
        "category_name": "ToDelete"
    })
    category_id = create_response.json()["id"]
    
    # Delete category
    response = test_client.delete(f"/categories/{category_id}")
    assert response.status_code == 200
    
    # Verify it's deleted (soft delete)
    get_response = test_client.get(f"/categories/{category_id}")
    assert get_response.status_code == 404


def test_get_leaf_categories(test_client):
    """Test getting only leaf categories."""
    # Create hierarchy
    parent = test_client.post("/categories/", json={"category_name": "Parent"}).json()
    child1 = test_client.post("/categories/", json={
        "category_name": "Child1",
        "parent_category_id": parent["id"]
    }).json()
    test_client.post("/categories/", json={
        "category_name": "Child2",
        "parent_category_id": parent["id"]
    })
    test_client.post("/categories/", json={
        "category_name": "Grandchild",
        "parent_category_id": child1["id"]
    })
    
    # Get leaf categories
    response = test_client.get("/categories/?leaf_only=true")
    assert response.status_code == 200
    data = response.json()
    
    # Only Child2 and Grandchild should be leaves
    leaf_names = [cat["category_name"] for cat in data if cat["is_leaf"]]
    assert "Parent" not in leaf_names
    assert "Child1" not in leaf_names