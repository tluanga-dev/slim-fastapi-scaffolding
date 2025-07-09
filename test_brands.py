#!/usr/bin/env python
"""Test script for brand functionality."""

import asyncio
import httpx
import json


async def test_brands():
    """Test basic brand operations."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("Testing Brand API...")
        
        # Clean up existing test brands first
        print("\n0. Cleaning up existing test brands...")
        response = await client.get(f"{base_url}/brands/?search=Nike")
        if response.status_code == 200:
            result = response.json()
            for brand in result['brands']:
                if brand['brand_name'] == 'Nike':
                    await client.delete(f"{base_url}/brands/{brand['id']}")
                    print("  - Deleted existing Nike brand")
        
        response = await client.get(f"{base_url}/brands/?search=Adidas")
        if response.status_code == 200:
            result = response.json()
            for brand in result['brands']:
                if brand['brand_name'] == 'Adidas':
                    await client.delete(f"{base_url}/brands/{brand['id']}")
                    print("  - Deleted existing Adidas brand")
        
        # 1. Create first brand
        print("\n1. Creating brand 'Nike'...")
        response = await client.post(f"{base_url}/brands/", json={
            "brand_name": "Nike",
            "brand_code": "NK",
            "description": "Just Do It - Athletic footwear and apparel",
            "created_by": "test_user"
        })
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            nike = response.json()
            print(f"Created: {nike['brand_name']} (ID: {nike['id']})")
            print(f"Code: {nike['brand_code']}, Active: {nike['is_active']}")
        else:
            print(f"Error: {response.json()}")
            return
        
        # 2. Create second brand
        print("\n2. Creating brand 'Adidas'...")
        response = await client.post(f"{base_url}/brands/", json={
            "brand_name": "Adidas",
            "brand_code": "AD",
            "description": "Impossible is Nothing",
            "created_by": "test_user"
        })
        if response.status_code == 201:
            adidas = response.json()
            print(f"Created: {adidas['brand_name']} (ID: {adidas['id']})")
        else:
            print(f"Error: {response.json()}")
        
        # 3. Try to create duplicate brand name
        print("\n3. Testing duplicate brand name validation...")
        response = await client.post(f"{base_url}/brands/", json={
            "brand_name": "Nike",
            "brand_code": "NIKE2",
            "created_by": "test_user"
        })
        if response.status_code == 400:
            print(f"✓ Correctly rejected duplicate: {response.json()['detail']}")
        else:
            print(f"✗ Unexpected response: {response.status_code}")
        
        # 4. Get all brands
        print("\n4. Getting all brands...")
        response = await client.get(f"{base_url}/brands/")
        if response.status_code == 200:
            result = response.json()
            print(f"Found {result['total']} brands:")
            for brand in result['brands']:
                display_name = f"{brand['brand_name']} ({brand['brand_code']})" if brand['brand_code'] else brand['brand_name']
                print(f"  - {display_name}")
        
        # 5. Search brands
        print("\n5. Searching for brands containing 'ik'...")
        response = await client.get(f"{base_url}/brands/search?q=ik")
        if response.status_code == 200:
            brands = response.json()
            print(f"Found {len(brands)} matching brands:")
            for brand in brands:
                print(f"  - {brand['brand_name']} ({brand['brand_code']})")
        
        # 6. Get brand by ID
        print(f"\n6. Getting brand by ID {nike['id']}...")
        response = await client.get(f"{base_url}/brands/{nike['id']}")
        if response.status_code == 200:
            brand = response.json()
            print(f"Retrieved: {brand['brand_name']}")
            print(f"Description: {brand['description']}")
        
        # 7. Update brand
        print(f"\n7. Updating Nike brand description...")
        response = await client.put(f"{base_url}/brands/{nike['id']}", json={
            "description": "Just Do It - World's leading athletic brand",
            "updated_by": "test_user"
        })
        if response.status_code == 200:
            updated = response.json()
            print(f"Updated description: {updated['description']}")
        
        # 8. Check brand name availability
        print("\n8. Checking brand name availability...")
        response = await client.get(f"{base_url}/brands/check-name-availability?name=Puma")
        if response.status_code == 200:
            result = response.json()
            print(f"'Puma' is {'available' if result['available'] else 'not available'}")
        
        response = await client.get(f"{base_url}/brands/check-name-availability?name=Nike")
        if response.status_code == 200:
            result = response.json()
            print(f"'Nike' is {'available' if result['available'] else 'not available'}")
        
        # 9. Get active brands
        print("\n9. Getting all active brands...")
        response = await client.get(f"{base_url}/brands/active")
        if response.status_code == 200:
            brands = response.json()
            print(f"Found {len(brands)} active brands")
        
        # 10. Update brand status
        print(f"\n10. Deactivating Nike brand...")
        response = await client.patch(f"{base_url}/brands/{nike['id']}/status", json={
            "is_active": False,
            "updated_by": "test_user"
        })
        if response.status_code == 200:
            updated = response.json()
            print(f"Brand active status: {updated['is_active']}")
        
        # 11. Soft delete brand
        print(f"\n11. Soft deleting Adidas brand...")
        response = await client.delete(f"{base_url}/brands/{adidas['id']}?deleted_by=test_user")
        if response.status_code == 204:
            print("Brand successfully deleted")
        
        # 12. Final count of active brands
        print("\n12. Final count of active brands...")
        response = await client.get(f"{base_url}/brands/?is_active=true")
        if response.status_code == 200:
            result = response.json()
            print(f"Active brands: {result['total']}")
        
        print("\n✅ Brand API test completed!")


if __name__ == "__main__":
    asyncio.run(test_brands())