import os
import sys
from unittest.mock import MagicMock, patch

# Mock the database engine creation to avoid connecting to real DB during import
with patch('sqlalchemy.create_engine') as mock_create_engine:
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    # Also mock check_and_migrate_db to do nothing
    with patch('app.database.check_and_migrate_db'):
        from app.main import app, get_db
        from app.models import Base, Translation

# Now proceed with setting up the test DB (SQLite)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the test DB
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_translation_with_field():
    # Mock the translation engine to avoid loading heavy models
    from app.translator import translation_engine
    translation_engine.translate = lambda text, lang: f"Translated {text}"
    translation_engine.supported_languages = {"es": "model"}
    # Mock models loaded check
    translation_engine.models = {"es": True}

    response = client.post(
        "/translate",
        json={
            "original_request_id": 1,
            "text": "Hello",
            "field_name": "name",
            "target_languages": ["es"]
        }
    )
    if response.status_code != 200:
        print(f"Response error: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["field_name"] == "name"
    assert data[0]["original_request_id"] == 1
    assert data[0]["translated_text"] == "Translated Hello"

def test_get_translations_filter():
    # Clear db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Create translations
    db = TestingSessionLocal()
    t1 = Translation(original_request_id=1, field_name="name", language="es", original_text="Name", translated_text="Nombre")
    t2 = Translation(original_request_id=1, field_name="description", language="es", original_text="Desc", translated_text="Descrip")
    db.add(t1)
    db.add(t2)
    db.commit()
    db.close()

    # Get all
    response = client.get("/translations/1")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Filter by field_name
    response = client.get("/translations/1?field_name=name")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["field_name"] == "name"
    assert data[0]["translated_text"] == "Nombre"

if __name__ == "__main__":
    try:
        test_create_translation_with_field()
        test_get_translations_filter()
        print("All translation service tests passed!")
    except Exception as e:
        print(f"Tests failed: {e}")
        import traceback
        traceback.print_exc()
