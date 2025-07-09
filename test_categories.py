#!/usr/bin/env python
"""Test script for category functionality."""

import asyncio
import httpx
import json

async def test_categories():
    """Test basic category operations."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("Testing Category API...")
        
        # 1. Create root category
        print("\n1. Creating root category 'Electronics'...")
        response = await client.post(f"{base_url}/categories/", json={
            "category_name": "Electronics",
            "display_order": 1
        })
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            electronics = response.json()
            print(f"Created: {electronics['category_name']} (ID: {electronics['id']})")
            print(f"Path: {electronics['category_path']}, Level: {electronics['category_level']}")
        else:
            print(f"Error: {response.json()}")
            return
        
        # 2. Create child category
        print("\n2. Creating child category 'Computers'...")
        response = await client.post(f"{base_url}/categories/", json={
            "category_name": "Computers",
            "parent_category_id": electronics['id'],
            "display_order": 1
        })
        if response.status_code == 200:
            computers = response.json()
            print(f"Created: {computers['category_name']} (ID: {computers['id']})")
            print(f"Path: {computers['category_path']}, Level: {computers['category_level']}")
        else:
            print(f"Error: {response.json()}")
        
        # 3. Get category tree
        print("\n3. Getting category tree...")
        response = await client.get(f"{base_url}/categories/tree")
        if response.status_code == 200:
            tree = response.json()
            print(f"Tree has {len(tree)} root categories")
            for root in tree:
                print_tree(root, 0)
        else:
            print(f"Error: {response.json()}")
        
        # 4. Get all categories
        print("\n4. Getting all root categories...")
        response = await client.get(f"{base_url}/categories/")
        if response.status_code == 200:
            categories = response.json()
            print(f"Found {len(categories)} root categories:")
            for cat in categories:
                print(f"  - {cat['category_name']} (Level {cat['category_level']})")
        
        # 5. Update category
        print(f"\n5. Updating 'Electronics' to 'Electronics & Gadgets'...")
        response = await client.put(f"{base_url}/categories/{electronics['id']}", json={
            "category_name": "Electronics & Gadgets"
        })
        if response.status_code == 200:
            updated = response.json()
            print(f"Updated: {updated['category_name']}")
            print(f"New path: {updated['category_path']}")
        
        print("\n✅ Category API test completed!")

def print_tree(node, level):
    """Print category tree with indentation."""
    indent = "  " * level
    print(f"{indent}- {node['category_name']} (Level {node['category_level']})")
    for child in node.get('children', []):
        print_tree(child, level + 1)

if __name__ == "__main__":
    asyncio.run(test_categories())