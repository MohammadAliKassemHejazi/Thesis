#!/usr/bin/env python3
"""
Test script for microservices architecture
"""
import requests
import time
import json

PRODUCT_SERVICE = "http://localhost:3000"
TRANSLATION_SERVICE = "http://localhost:3001"

def print_section(title):
    print("\n" + "="*50)
    print(title)
    print("="*50)

def test_health_checks():
    print_section("1. Testing Health Checks")
    
    print("\n📊 Product Service Health:")
    response = requests.get(f"{PRODUCT_SERVICE}/health")
    print(json.dumps(response.json(), indent=2))
    
    print("\n📊 Translation Service Health:")
    response = requests.get(f"{TRANSLATION_SERVICE}/health")
    print(json.dumps(response.json(), indent=2))

def test_create_product():
    print_section("2. Creating Test Product")
    
    product_data = {
        "name": "Wireless Headphones",
        "description": "High-quality noise-cancelling headphones",
        "price": 199.99,
        "auto_translate": True,
        "target_languages": ["es", "fr", "de"]
    }
    
    print(f"\n📝 Creating product: {product_data['name']}")
    response = requests.post(
        f"{PRODUCT_SERVICE}/products",
        json=product_data
    )
    product = response.json()
    print(json.dumps(product, indent=2))
    
    return product['id']

def test_translations(product_id):
    print_section("3. Testing Translations")
    
    print("\n⏳ Waiting 5 seconds for translations to complete...")
    time.sleep(5)
    
    languages = [
        ("en", "English"),
        ("es", "Spanish"),
        ("fr", "French"),
        ("de", "German")
    ]
    
    for lang_code, lang_name in languages:
        print(f"\n🌍 Fetching product in {lang_name} ({lang_code}):")
        response = requests.get(f"{PRODUCT_SERVICE}/products/{product_id}?lang={lang_code}")
        print(json.dumps(response.json(), indent=2))

def test_direct_translation_access(product_id):
    print_section("4. Direct Translation Service Access")
    
    print(f"\n🔍 Fetching all translations for product {product_id}:")
    response = requests.get(f"{TRANSLATION_SERVICE}/translations/{product_id}")
    translations = response.json()
    print(json.dumps(translations, indent=2))

def test_multiple_products():
    print_section("5. Testing Multiple Products")
    
    products = [
        {
            "name": "Bluetooth Speaker",
            "description": "Portable waterproof speaker",
            "price": 79.99,
            "auto_translate": True,
            "target_languages": ["es", "fr"]
        },
        {
            "name": "Smart Watch",
            "description": "Fitness tracker with heart rate monitor",
            "price": 299.99,
            "auto_translate": True,
            "target_languages": ["es", "de"]
        }
    ]
    
    for product_data in products:
        print(f"\n📝 Creating: {product_data['name']}")
        response = requests.post(f"{PRODUCT_SERVICE}/products", json=product_data)
        print(json.dumps(response.json(), indent=2))
    
    print("\n⏳ Waiting 5 seconds for translations...")
    time.sleep(5)
    
    print("\n📋 Listing all products in Spanish:")
    response = requests.get(f"{PRODUCT_SERVICE}/products?lang=es")
    products_list = response.json()
    print(json.dumps(products_list, indent=2))

def test_human_in_the_loop_features():
    print_section("6. Human-in-the-Loop Features")

    print("\n🔍 Getting pending translations:")
    response = requests.get(f"{TRANSLATION_SERVICE}/translations/pending")
    pending_translations = response.json()
    print(json.dumps(pending_translations, indent=2))

    if pending_translations:
        first_pending = pending_translations[0]
        translation_id = first_pending["id"]
        original_translated_text = first_pending["translated_text"]
        edited_text = f"{original_translated_text} (human-edited)"
        feedback = "Improved clarity and tone."
        reviewer_name = "Test Reviewer"

        print(f"\n✍️ Submitting edit for translation ID {translation_id}:")
        edit_data = {
            "edited_text": edited_text,
            "feedback": feedback,
            "edited_by": reviewer_name
        }
        response = requests.put(
            f"{TRANSLATION_SERVICE}/translations/{translation_id}/edit",
            json=edit_data
        )
        print(json.dumps(response.json(), indent=2))

        print(f"\n✅ Verifying edited translation ID {translation_id}:")
        response = requests.get(f"{TRANSLATION_SERVICE}/translations/{first_pending["original_request_id"]}")
        all_translations_for_product = response.json()
        edited_translation = next((t for t in all_translations_for_product if t["id"] == translation_id), None)
        print(json.dumps(edited_translation, indent=2))

    else:
        print("\nℹ️ No pending translations to edit.")

    print("\n📊 Getting translation statistics:")
    response = requests.get(f"{TRANSLATION_SERVICE}/translations/statistics")
    print(json.dumps(response.json(), indent=2))

def main():
    print("\n" + "🚀 " * 20)
    print("MICROSERVICES TRANSLATION SYSTEM - TEST SUITE")
    print("🚀 " * 20)
    
    try:
        # Run tests
        test_health_checks()
        product_id = test_create_product()
        test_translations(product_id)
        test_direct_translation_access(product_id)
        test_multiple_products()
        test_human_in_the_loop_features()
        
        print_section("✅ All Tests Completed Successfully!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to services.")
        print("Make sure the services are running with: docker-compose up")
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    main()
