#!/bin/bash

# Rental Management System API - Authentication Examples
# Base URL for the API
BASE_URL="http://localhost:8000"

echo "=== Rental Management System API - Authentication Examples ==="
echo

# 1. Register a new user
echo "1. Registering a new user..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "email": "demo@example.com",
    "password": "SecurePass123!",
    "first_name": "Demo",
    "last_name": "User"
  }')

echo "Registration Response:"
echo "$REGISTER_RESPONSE" | python3 -m json.tool
echo

# 2. Login user and get token
echo "2. Logging in user..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "SecurePass123!"
  }')

echo "Login Response:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool

# Extract access token for subsequent requests
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "Failed to get access token. Exiting..."
    exit 1
fi

echo "Access Token: $ACCESS_TOKEN"
echo

# 3. Get current user information
echo "3. Getting current user information..."
USER_INFO_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "User Info Response:"
echo "$USER_INFO_RESPONSE" | python3 -m json.tool
echo

# 4. Update user profile
echo "4. Updating user profile..."
UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Demo Updated",
    "last_name": "User Updated",
    "phone_number": "+1234567890"
  }')

echo "Update Profile Response:"
echo "$UPDATE_RESPONSE" | python3 -m json.tool
echo

# 5. Change password
echo "5. Changing password..."
CHANGE_PASSWORD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/change-password" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "SecurePass123!",
    "new_password": "NewSecurePass456!"
  }')

echo "Change Password Response:"
echo "$CHANGE_PASSWORD_RESPONSE" | python3 -m json.tool
echo

# 6. Refresh token (extract refresh token from login response)
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])" 2>/dev/null)

if [ ! -z "$REFRESH_TOKEN" ]; then
    echo "6. Refreshing access token..."
    REFRESH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/refresh" \
      -H "Content-Type: application/json" \
      -d "{
        \"refresh_token\": \"$REFRESH_TOKEN\"
      }")
    
    echo "Refresh Token Response:"
    echo "$REFRESH_RESPONSE" | python3 -m json.tool
    echo
fi

# 7. Get user statistics (admin endpoint)
echo "7. Getting user statistics..."
STATS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/auth/statistics" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "User Statistics Response:"
echo "$STATS_RESPONSE" | python3 -m json.tool
echo

# 8. Logout user
echo "8. Logging out user..."
LOGOUT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Logout Response:"
echo "$LOGOUT_RESPONSE" | python3 -m json.tool
echo

echo "=== Authentication Examples Complete ==="
echo
echo "Note: Some endpoints may require admin privileges."
echo "The demo user created above has basic user permissions."