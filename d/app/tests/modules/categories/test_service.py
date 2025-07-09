import pytest
from uuid import uuid4
from app.modules.categories.service import CategoryService
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate


@pytest.mark.asyncio
async def test_create_root_category(test_session):
    """Test creating a root category through service."""
    repo = CategoryRepository(test_session)
    service = CategoryService(repo)
    
    category_data = CategoryCreate(
        category_name="Electronics",
        display_order=1
    )
    
    category = await service.create_category(category_data, "test_user")
    assert category.id is not None
    assert category.category_name == "Electronics"
    assert category.category_level == 1
    assert category.category_path == "Electronics"
    assert category.is_leaf == True
    assert category.created_by == "test_user"


@pytest.mark.asyncio
async def test_create_child_category(test_session):
    """Test creating a child category."""
    repo = CategoryRepository(test_session)
    service = CategoryService(repo)
    
    # Create parent
    parent_data = CategoryCreate(category_name="Electronics")
    parent = await service.create_category(parent_data)
    
    # Create child
    child_data = CategoryCreate(
        category_name="Computers",
        parent_category_id=parent.id
    )
    child = await service.create_category(child_data)
    
    assert child.category_level == 2
    assert child.category_path == "Electronics/Computers"
    assert child.parent_category_id == parent.id
    
    # Verify parent is no longer a leaf
    updated_parent = await service.get_category(parent.id)
    assert updated_parent.is_leaf == False


@pytest.mark.asyncio
async def test_duplicate_category_name(test_session):
    """Test that duplicate names under same parent are not allowed."""
    repo = CategoryRepository(test_session)
    service = CategoryService(repo)
    
    # Create first category
    await service.create_category(CategoryCreate(category_name="Electronics"))
    
    # Try to create duplicate
    with pytest.raises(ValueError) as exc_info:
        await service.create_category(CategoryCreate(category_name="Electronics"))
    
    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_category_name(test_session):
    """Test updating category name and path propagation."""
    repo = CategoryRepository(test_session)
    service = CategoryService(repo)
    
    # Create parent and child
    parent = await service.create_category(CategoryCreate(category_name="Eletronics"))  # Typo
    child = await service.create_category(
        CategoryCreate(category_name="Computers", parent_category_id=parent.id)
    )
    
    # Update parent name
    updated = await service.update_category(
        parent.id,
        CategoryUpdate(category_name="Electronics"),  # Fix typo
        "updater"
    )
    
    assert updated.category_name == "Electronics"
    assert updated.category_path == "Electronics"
    assert updated.updated_by == "updater"
    
    # Check child path was updated
    updated_child = await service.get_category(child.id)
    assert updated_child.category_path == "Electronics/Computers"


@pytest.mark.asyncio
async def test_delete_category_with_children(test_session):
    """Test deleting a category with children."""
    repo = CategoryRepository(test_session)
    service = CategoryService(repo)
    
    # Create hierarchy
    parent = await service.create_category(CategoryCreate(category_name="Parent"))
    child1 = await service.create_category(
        CategoryCreate(category_name="Child1", parent_category_id=parent.id)
    )
    child2 = await service.create_category(
        CategoryCreate(category_name="Child2", parent_category_id=parent.id)
    )
    grandchild = await service.create_category(
        CategoryCreate(category_name="Grandchild", parent_category_id=child1.id)
    )
    
    # Delete parent
    success = await service.delete_category(parent.id, "deleter")
    assert success == True
    
    # All should be soft deleted
    assert await service.get_category(parent.id) is None
    assert await service.get_category(child1.id) is None
    assert await service.get_category(child2.id) is None
    assert await service.get_category(grandchild.id) is None


@pytest.mark.asyncio
async def test_move_category(test_session):
    """Test moving a category to a new parent."""
    repo = CategoryRepository(test_session)
    service = CategoryService(repo)
    
    # Create categories
    electronics = await service.create_category(CategoryCreate(category_name="Electronics"))
    home = await service.create_category(CategoryCreate(category_name="Home"))
    computers = await service.create_category(
        CategoryCreate(category_name="Computers", parent_category_id=electronics.id)
    )
    
    # Move computers from electronics to home
    moved = await service.move_category(computers.id, home.id, "mover")
    
    assert moved.parent_category_id == home.id
    assert moved.category_path == "Home/Computers"
    assert moved.category_level == 2
    
    # Check old parent is now a leaf
    updated_electronics = await service.get_category(electronics.id)
    assert updated_electronics.is_leaf == True
    
    # Check new parent is not a leaf
    updated_home = await service.get_category(home.id)
    assert updated_home.is_leaf == False


@pytest.mark.asyncio
async def test_circular_reference_prevention(test_session):
    """Test that moving a category to its descendant is prevented."""
    repo = CategoryRepository(test_session)
    service = CategoryService(repo)
    
    # Create hierarchy
    parent = await service.create_category(CategoryCreate(category_name="Parent"))
    child = await service.create_category(
        CategoryCreate(category_name="Child", parent_category_id=parent.id)
    )
    grandchild = await service.create_category(
        CategoryCreate(category_name="Grandchild", parent_category_id=child.id)
    )
    
    # Try to move parent under grandchild (circular reference)
    with pytest.raises(ValueError) as exc_info:
        await service.move_category(parent.id, grandchild.id)
    
    assert "circular reference" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_leaf_categories(test_session):
    """Test getting only leaf categories."""
    repo = CategoryRepository(test_session)
    service = CategoryService(repo)
    
    # Create hierarchy
    parent = await service.create_category(CategoryCreate(category_name="Parent"))
    child1 = await service.create_category(
        CategoryCreate(category_name="Child1", parent_category_id=parent.id)
    )
    await service.create_category(
        CategoryCreate(category_name="Child2", parent_category_id=parent.id)
    )
    await service.create_category(
        CategoryCreate(category_name="Grandchild", parent_category_id=child1.id)
    )
    
    # Get leaf categories
    leaves = await service.get_leaf_categories()
    leaf_names = [cat.category_name for cat in leaves]
    
    # Only Child2 and Grandchild should be leaves
    assert "Parent" not in leaf_names
    assert "Child1" not in leaf_names
    assert "Child2" in leaf_names
    assert "Grandchild" in leaf_names