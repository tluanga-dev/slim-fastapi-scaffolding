#!/bin/bash

# Rental Management System API - Customer Management Examples
BASE_URL="http://localhost:8000"

echo "=== Rental Management System API - Customer Management Examples ==="
echo

# First, we need to login and get a token
echo "Logging in to get access token..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "NewSecurePass456!"
  }')

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "Failed to get access token. Please run auth_examples.sh first."
    exit 1
fi

echo "Access Token obtained: ${ACCESS_TOKEN:0:20}..."
echo

# 1. Create individual customer
echo "1. Creating individual customer..."
INDIVIDUAL_CUSTOMER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/customers" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_type": "INDIVIDUAL",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1-555-0123",
    "address": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
    "date_of_birth": "1985-06-15",
    "gender": "MALE",
    "preferred_language": "EN",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+1-555-0124"
  }')

echo "Individual Customer Response:"
echo "$INDIVIDUAL_CUSTOMER_RESPONSE" | python3 -m json.tool

# Extract customer ID for subsequent operations
INDIVIDUAL_CUSTOMER_ID=$(echo "$INDIVIDUAL_CUSTOMER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "Individual Customer ID: $INDIVIDUAL_CUSTOMER_ID"
echo

# 2. Create business customer
echo "2. Creating business customer..."
BUSINESS_CUSTOMER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/customers" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_type": "BUSINESS",
    "business_name": "Acme Corporation",
    "email": "contact@acme.com",
    "phone_number": "+1-555-0200",
    "address": "456 Business Ave",
    "city": "Chicago",
    "state": "IL",
    "postal_code": "60601",
    "country": "USA",
    "tax_id": "12-3456789",
    "business_registration_number": "REG123456",
    "industry": "Technology",
    "website": "https://www.acme.com",
    "primary_contact_name": "Alice Smith",
    "primary_contact_email": "alice@acme.com",
    "primary_contact_phone": "+1-555-0201"
  }')

echo "Business Customer Response:"
echo "$BUSINESS_CUSTOMER_RESPONSE" | python3 -m json.tool

BUSINESS_CUSTOMER_ID=$(echo "$BUSINESS_CUSTOMER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "Business Customer ID: $BUSINESS_CUSTOMER_ID"
echo

# 3. List all customers
echo "3. Listing all customers..."
LIST_CUSTOMERS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/customers?page=1&page_size=10&sort_by=created_at&sort_order=desc" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "List Customers Response:"
echo "$LIST_CUSTOMERS_RESPONSE" | python3 -m json.tool
echo

# 4. Get specific customer by ID
if [ ! -z "$INDIVIDUAL_CUSTOMER_ID" ]; then
    echo "4. Getting individual customer by ID..."
    GET_CUSTOMER_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/customers/$INDIVIDUAL_CUSTOMER_ID" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    echo "Get Customer Response:"
    echo "$GET_CUSTOMER_RESPONSE" | python3 -m json.tool
    echo
fi

# 5. Update customer information
if [ ! -z "$INDIVIDUAL_CUSTOMER_ID" ]; then
    echo "5. Updating customer information..."
    UPDATE_CUSTOMER_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/v1/customers/$INDIVIDUAL_CUSTOMER_ID" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "phone_number": "+1-555-0125",
        "address": "789 New Address St",
        "city": "Brooklyn",
        "postal_code": "11201",
        "notes": "Updated contact information"
      }')
    
    echo "Update Customer Response:"
    echo "$UPDATE_CUSTOMER_RESPONSE" | python3 -m json.tool
    echo
fi

# 6. Search customers
echo "6. Searching customers..."
SEARCH_CUSTOMERS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/customers/search" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "john",
    "filters": {
      "customer_type": "INDIVIDUAL",
      "status": "ACTIVE",
      "city": "Brooklyn"
    },
    "sort_by": "last_name",
    "sort_order": "asc",
    "page": 1,
    "page_size": 5
  }')

echo "Search Customers Response:"
echo "$SEARCH_CUSTOMERS_RESPONSE" | python3 -m json.tool
echo

# 7. Update customer status
if [ ! -z "$INDIVIDUAL_CUSTOMER_ID" ]; then
    echo "7. Updating customer status..."
    UPDATE_STATUS_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/v1/customers/$INDIVIDUAL_CUSTOMER_ID/status" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "status": "ACTIVE",
        "reason": "Customer verification completed"
      }')
    
    echo "Update Status Response:"
    echo "$UPDATE_STATUS_RESPONSE" | python3 -m json.tool
    echo
fi

# 8. Update customer credit information
if [ ! -z "$INDIVIDUAL_CUSTOMER_ID" ]; then
    echo "8. Updating customer credit information..."
    UPDATE_CREDIT_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/v1/customers/$INDIVIDUAL_CUSTOMER_ID/credit" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "credit_limit": 5000.00,
        "credit_rating": "GOOD",
        "credit_check_date": "2024-01-01",
        "notes": "Good payment history"
      }')
    
    echo "Update Credit Response:"
    echo "$UPDATE_CREDIT_RESPONSE" | python3 -m json.tool
    echo
fi

# 9. Get customer statistics
echo "9. Getting customer statistics..."
CUSTOMER_STATS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/customers/statistics" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Customer Statistics Response:"
echo "$CUSTOMER_STATS_RESPONSE" | python3 -m json.tool
echo

# 10. Get customer transactions (if customer has any)
if [ ! -z "$INDIVIDUAL_CUSTOMER_ID" ]; then
    echo "10. Getting customer transactions..."
    CUSTOMER_TRANSACTIONS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/customers/$INDIVIDUAL_CUSTOMER_ID/transactions?page=1&page_size=10" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    echo "Customer Transactions Response:"
    echo "$CUSTOMER_TRANSACTIONS_RESPONSE" | python3 -m json.tool
    echo
fi

# 11. Create customer address
if [ ! -z "$INDIVIDUAL_CUSTOMER_ID" ]; then
    echo "11. Adding customer address..."
    ADD_ADDRESS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/customers/$INDIVIDUAL_CUSTOMER_ID/addresses" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "address_type": "BILLING",
        "address": "999 Billing Street",
        "city": "Manhattan",
        "state": "NY",
        "postal_code": "10002",
        "country": "USA",
        "is_default": false
      }')
    
    echo "Add Address Response:"
    echo "$ADD_ADDRESS_RESPONSE" | python3 -m json.tool
    echo
fi

# 12. Export customer data
if [ ! -z "$INDIVIDUAL_CUSTOMER_ID" ]; then
    echo "12. Exporting customer data..."
    EXPORT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/customers/$INDIVIDUAL_CUSTOMER_ID/export" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    echo "Export Customer Response:"
    echo "$EXPORT_RESPONSE" | python3 -m json.tool
    echo
fi

echo "=== Customer Management Examples Complete ==="
echo
echo "Created customers:"
echo "- Individual Customer ID: $INDIVIDUAL_CUSTOMER_ID"
echo "- Business Customer ID: $BUSINESS_CUSTOMER_ID"