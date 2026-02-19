#!/bin/bash

# Test script for microservices
echo "=========================================="
echo "Testing Microservices Architecture"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URLs
PRODUCT_SERVICE="http://localhost:3000"
TRANSLATION_SERVICE="http://localhost:3001"

echo -e "${YELLOW}1. Testing Product Service Health...${NC}"
curl -s "$PRODUCT_SERVICE/health" | jq '.'
echo ""

echo -e "${YELLOW}2. Testing Translation Service Health...${NC}"
curl -s "$TRANSLATION_SERVICE/health" | jq '.'
echo ""

echo -e "${YELLOW}3. Creating a new product (Wireless Headphones)...${NC}"
PRODUCT_RESPONSE=$(curl -s -X POST "$PRODUCT_SERVICE/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Headphones",
    "description": "High-quality noise-cancelling headphones",
    "price": 199.99,
    "auto_translate": true,
    "target_languages": ["es", "fr", "de"]
  }')
echo "$PRODUCT_RESPONSE" | jq '.'
PRODUCT_ID=$(echo "$PRODUCT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}Product created with ID: $PRODUCT_ID${NC}"
echo ""

echo -e "${YELLOW}4. Waiting for translations to complete (5 seconds)...${NC}"
sleep 5
echo ""

echo -e "${YELLOW}5. Fetching product in English...${NC}"
curl -s "$PRODUCT_SERVICE/products/$PRODUCT_ID?lang=en" | jq '.'
echo ""

echo -e "${YELLOW}6. Fetching product in Spanish...${NC}"
curl -s "$PRODUCT_SERVICE/products/$PRODUCT_ID?lang=es" | jq '.'
echo ""

echo -e "${YELLOW}7. Fetching product in French...${NC}"
curl -s "$PRODUCT_SERVICE/products/$PRODUCT_ID?lang=fr" | jq '.'
echo ""

echo -e "${YELLOW}8. Fetching product in German...${NC}"
curl -s "$PRODUCT_SERVICE/products/$PRODUCT_ID?lang=de" | jq '.'
echo ""

echo -e "${YELLOW}9. Checking translations directly from Translation Service...${NC}"
curl -s "$TRANSLATION_SERVICE/translations/$PRODUCT_ID" | jq '.'
echo ""

echo -e "${YELLOW}10. Creating another product (Bluetooth Speaker)...${NC}"
PRODUCT_RESPONSE2=$(curl -s -X POST "$PRODUCT_SERVICE/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bluetooth Speaker",
    "description": "Portable waterproof speaker with amazing sound",
    "price": 79.99,
    "auto_translate": true,
    "target_languages": ["es", "fr"]
  }')
echo "$PRODUCT_RESPONSE2" | jq '.'
PRODUCT_ID2=$(echo "$PRODUCT_RESPONSE2" | jq -r '.id')
echo ""

echo -e "${YELLOW}11. Waiting for translations (5 seconds)...${NC}"
sleep 5
echo ""

echo -e "${YELLOW}12. Listing all products in Spanish...${NC}"
curl -s "$PRODUCT_SERVICE/products?lang=es" | jq '.'
echo ""

echo -e "${YELLOW}13. Getting pending translations from Translation Service...${NC}"
PENDING_TRANSLATIONS=$(curl -s "$TRANSLATION_SERVICE/translations/pending" | jq ".")
echo "$PENDING_TRANSLATIONS" | jq "."
FIRST_PENDING_ID=$(echo "$PENDING_TRANSLATIONS" | jq -r ".[0].id")
FIRST_PENDING_TEXT=$(echo "$PENDING_TRANSLATIONS" | jq -r ".[0].translated_text")

if [ -n "$FIRST_PENDING_ID" ] && [ "$FIRST_PENDING_ID" != "null" ]; then
  echo -e "${YELLOW}14. Submitting an edit for translation ID $FIRST_PENDING_ID...${NC}"
  EDITED_TEXT="${FIRST_PENDING_TEXT} (human-edited)"
  EDIT_RESPONSE=$(curl -s -X PUT "$TRANSLATION_SERVICE/translations/$FIRST_PENDING_ID/edit" \
    -H "Content-Type: application/json" \
    -d "{\"edited_text\": \"$EDITED_TEXT\", \"feedback\": \"Improved clarity\", \"edited_by\": \"Test Reviewer\"}")
  echo "$EDIT_RESPONSE" | jq "."
  echo ""

  echo -e "${YELLOW}15. Verifying the edited translation...${NC}"
  curl -s "$TRANSLATION_SERVICE/translations/$PRODUCT_ID" | jq "."
  echo ""
else
  echo -e "${YELLOW}14. No pending translations to edit.${NC}"
fi

echo -e "${YELLOW}16. Getting translation statistics...${NC}"
curl -s "$TRANSLATION_SERVICE/translations/statistics" | jq "."
echo ""

echo -e "${GREEN}=========================================="
echo "All tests completed!"
echo "==========================================${NC}"
