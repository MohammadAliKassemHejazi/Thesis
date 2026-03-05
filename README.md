# Microservices Product Translation System

This project implements a microservice architecture for a product translation system. It consists of two main services that work together to provide automated product translations using local AI models.

1.  **Product Service** (Node.js/Express.js): The core service for managing product inventory. It handles CRUD operations and orchestrates translations by communicating with the Translation Service.
2.  **Translation Service** (Python/FastAPI): A specialized service that performs text translation using local AI models (Hugging Face MarianMT/OPUS-MT) and manages translation records.

Both services are containerized using Docker and orchestrated with Docker Compose, each with its own isolated PostgreSQL database.

## Architecture Overview

-   **Product Service**: Built with Node.js, Express, and Sequelize ORM. It manages the product lifecycle and treats translations as an external dependency. It supports a modular architecture with controllers, services, and routes.
-   **Translation Service**: Built with Python and FastAPI. It hosts local AI models for English-to-X translation (Spanish, French, German) and provides an API for managing these translations. It also includes an embedded dashboard for monitoring.
-   **Data Isolation**: Each service owns its data. `product-service` uses `products_db`, and `translation-service` uses `translations_db`.
-   **Distributed Transactions**: The system implements a strict deletion pattern where a product deletion in the Product Service triggers a synchronous deletion of associated translations in the Translation Service before finalizing the local delete.

## Features

-   **Local AI Translation**: Uses Hugging Face `MarianMT` models (OPUS-MT family) running locally. No external APIs or costs.
-   **Supported Languages**: Currently supports translation from English to **Spanish (es)**, **French (fr)**, and **German (de)**.
-   **Embedded Dashboard**: The Translation Service includes a lightweight dashboard at `/dashboard` for viewing translation statistics and status.
-   **Modular Codebase**:
    -   `product-service`: Controller-Service-Repository pattern with Sequelize.
    -   `translation-service`: FastAPI Router-Schema pattern with SQLAlchemy and Alembic.
-   **Swagger Documentation**: Both services provide interactive API documentation via Swagger UI.

## Project Structure

```
microservices-translation-project/
├── product-service/             # Node.js Product Management Service
│   ├── src/
│   │   ├── config/              # Configuration (Sequelize, Swagger)
│   │   ├── controllers/         # Request handlers
│   │   ├── models/              # Sequelize models
│   │   ├── routes/              # API route definitions
│   │   ├── services/            # Business logic (Product & Translation integration)
│   │   ├── app.js               # Express app setup
│   │   └── server.js            # Server entry point
│   ├── Dockerfile
│   └── package.json
├── translation-service/         # Python/FastAPI AI Translation Service
│   ├── app/
│   │   ├── api/                 # API endpoints (v1)
│   │   ├── core/                # Core configuration
│   │   ├── crud/                # Database operations
│   │   ├── schemas/             # Pydantic models
│   │   ├── templates/           # HTML templates (Dashboard)
│   │   ├── database.py          # Database connection
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models.py            # SQLAlchemy models
│   │   └── translator.py        # AI Model logic (MarianMT)
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml           # Orchestration for services and DBs
├── test_services.py             # Python integration test suite
└── README.md
```

## Getting Started

### Prerequisites

-   [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
-   `python3` and `pip` (for running the test script locally)

### Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd microservices-translation-project
    ```

2.  **Build and Run:**
    ```bash
    docker compose up --build -d
    ```
    This will start:
    -   `product-service` (Port 3000)
    -   `translation-service` (Port 3001)
    -   `product-db` (PostgreSQL 15)
    -   `translation-db` (PostgreSQL 15)

3.  **Verify Services:**
    Check the status of your containers:
    ```bash
    docker compose ps
    ```
    *Note: The Translation Service will download AI models (~300MB each) on the first startup. This may take a few minutes.*

## Usage and Testing

### Accessing the Services

-   **Product Service**: `http://localhost:3000`
    -   Swagger UI: `http://localhost:3000/docs`
    -   API Root: `/products`
-   **Translation Service**: `http://localhost:3001`
    -   Swagger UI: `http://localhost:3001/docs`
    -   Dashboard: `http://localhost:3001/dashboard`

### Running the Test Suite

A comprehensive Python test script is provided to verify the entire flow, including product creation, asynchronous translation, retrieval, and synchronized deletion.

```bash
# Install requests if needed
pip install requests

# Run the test suite
python3 test_services.py
```

### Manual Testing with cURL

1.  **Create a Product** (Triggers translation):
    ```bash
    curl -X POST http://localhost:3000/products \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Smart Coffee Maker",
        "description": "Programmable coffee maker with wifi",
        "price": 129.99,
        "target_languages": ["es", "fr"]
      }'
    ```

2.  **Retrieve in Spanish** (Wait a few seconds for AI processing):
    ```bash
    # Replace <ID> with the ID from the previous step
    curl "http://localhost:3000/products/<ID>?lang=es"
    ```

3.  **View Translation Dashboard**:
    Open `http://localhost:3001/dashboard` in your browser to see translation statistics.

## Development Notes

-   **Database Migrations**: The `translation-service` uses Alembic. Migrations are run automatically on startup in `main.py`.
-   **Model Caching**: AI models are cached in the `model_cache` Docker volume to prevent re-downloading on every restart.
-   **Extending Languages**: To add a new language, update `translation-service/app/translator.py` with the corresponding Hugging Face model key.

## Troubleshooting

-   **Service Crashes (OOM)**: The AI models require significant memory. Ensure your Docker Desktop has at least 4GB of RAM allocated.
-   **"Translation not found"**: If you request a translation immediately after creation, it may return the English fallback or a 404 from the translation service. The system is asynchronous; give it a few seconds.

---
**Author**: Manus AI

## How the System Works & Editing Translations

The system follows a choreographed sequence for managing products and their translated text:

1.  **Product Creation (Fire-and-Forget Translation)**:
    *   When a user creates a new product in the Product Service (`POST /products`), they can specify a list of `target_languages` (e.g., `["es", "fr"]`).
    *   The Product Service saves the English product details to its own database.
    *   It then asynchronously issues a single `POST /translate` request to the Translation Service, passing both the `name` and `description` to be translated, and immediately returns a success response to the client.

2.  **Asynchronous Translation & Validation**:
    *   The Translation Service receives the request and processes it using local Hugging Face `MarianMT` AI models.
    *   For quality assurance, it performs a **back-translation** validation step: it translates the generated text back to English and calculates a confidence score using a sequence matcher.
    *   The translated `name` and `description` are saved in a single translation record per target language in the `translations_db`.

3.  **Retrieving Localized Products**:
    *   Clients fetch products via the Product Service (`GET /products` or `GET /products/:id`) and can pass a `?lang=es` query parameter.
    *   The Product Service dynamically queries the Translation Service for the localized data and merges it into the response. If the translation isn't ready or doesn't exist, it defaults back to English.

4.  **Editing and Correcting Translations**:
    *   Because AI translations aren't perfect, the system includes a **Dashboard** (`GET /dashboard` on Port 3001).
    *   Users can navigate to the dashboard to view translation statistics (completed, pending, average confidence).
    *   If a translation is inaccurate, a user can manually edit it via the dashboard, which triggers the `PUT /translations/{translation_id}/edit` endpoint.
    *   *Note: Active AI fine-tuning based on human edits is not implemented; the system prioritizes a robust manual override mechanism.*

5.  **Product Updates**:
    *   If a product is updated in the Product Service (`PUT /products/:id`) with new `target_languages`, the Translation Service strictly replaces existing records. It deletes the old translations for the specified languages within a single database transaction and creates new ones, ensuring data integrity. Unspecified languages are preserved.

6.  **Synchronized Deletion**:
    *   Deleting a product enforces a strict distributed transaction pattern.
    *   When `DELETE /products/:id` is called, the Product Service **must** successfully invoke `DELETE /translations/product/{original_request_id}` on the Translation Service first.
    *   Only if the Translation Service confirms the hard deletion of all associated translations will the Product Service finalize the removal of the product from its own database.

## API Endpoints

### Product Service (Port 3000)

*   **`GET /`**
    *   **Description**: Returns basic information about the Product Service.
*   **`GET /health`**
    *   **Description**: Health check endpoint to verify the service is running.
*   **`POST /products`**
    *   **Description**: Creates a new product and optionally triggers asynchronous translations if `target_languages` are provided.
    *   **Body**: `{"name": "...", "description": "...", "price": 0.0, "target_languages": ["es", "fr"]}`
*   **`GET /products`**
    *   **Description**: Retrieves a list of all products with pagination (`skip`, `limit`) and an optional `lang` query parameter to fetch localized details.
*   **`GET /products/:id`**
    *   **Description**: Retrieves a single product by its ID. An optional `lang` query parameter can be passed to get localized details.
*   **`PUT /products/:id`**
    *   **Description**: Updates an existing product and triggers a re-translation if `target_languages` are provided.
*   **`DELETE /products/:id`**
    *   **Description**: Deletes a product by ID. Triggers a synchronous deletion of associated translations in the Translation Service before removing the local record.

### Translation Service (Port 3001)

*   **`GET /`**
    *   **Description**: Returns basic information about the Translation Service.
*   **`GET /health`**
    *   **Description**: Health check endpoint to verify the service is running and models are loaded.
*   **`POST /translate`**
    *   **Description**: Accepts a text payload, translates it into the specified target languages using local AI models, and stores the results in the database.
*   **`GET /translations`**
    *   **Description**: Lists all translations in the database with pagination parameters (`skip`, `limit`).
*   **`GET /translations/{original_request_id}`**
    *   **Description**: Fetches all translations associated with a specific product ID (referred to as `original_request_id`). Can be filtered by `lang`.
*   **`GET /translations/statistics`**
    *   **Description**: Returns translation statistics, such as total counts per language and pending status. Used by the dashboard.
*   **`PUT /translations/{translation_id}/edit`**
    *   **Description**: Updates an existing translation record, typically used for manual edits or corrections from the dashboard.
*   **`DELETE /translations/{translation_id}`**
    *   **Description**: Deletes a specific translation record by its ID.
*   **`DELETE /translations/product/{original_request_id}`**
    *   **Description**: Deletes all translation records associated with a specific product ID. This endpoint is called by the Product Service during product deletion.
*   **`GET /dashboard`**
    *   **Description**: Serves an embedded HTML dashboard for monitoring translation statistics, viewing status, and manually editing translations without requiring a separate frontend service.
