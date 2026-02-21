# Microservices Product Translation System

This project implements a microservice architecture for a product translation system, as described in the initial requirements. It consists of two main services:

1.  **Main Product Service** (Node.js/Express.js): Manages product information and interacts with the Translation Microservice for language support.
2.  **Translation Microservice** (Python/FastAPI): Handles text translation using a local AI model (OPUS-MT) and stores translations.

Both services use their respective frameworks for APIs and PostgreSQL as their respective databases. The entire system is containerized using Docker and orchestrated with Docker Compose.

## Architecture Overview

-   **Main Product Service** (Node.js/Express.js): Manages products, stores them in `products_db`, and calls the Translation Microservice to get translations.
-   **Translation Microservice** (Python/FastAPI): Hosts local AI models (Hugging Face OPUS-MT) for translation, stores translations in `translations_db`.
-   **PostgreSQL Databases**: Two separate instances, `product-db` and `translation-db`, for data isolation.
-   **Docker & Docker Compose**: For containerization and orchestration of all services and databases.

## Features

-   **Private & Secure Translations**: No external AI services; all translations happen locally.
-   **Loose Coupling**: Services are independent, enhancing reliability and scalability.
-   **Multi-language Support**: Easily extendable to support more languages.
-   **RESTful APIs**: Clear and well-defined API endpoints for inter-service communication.
-   **Containerized Deployment**: Easy to deploy and manage using Docker.

## Project Structure

```
microservices-translation-project/
├── product-service/
│   ├── src/
│   │   ├── database.js
│   │   ├── index.js
│   │   └── translationClient.js
│   ├── Dockerfile
│   ├── package.json
│   └── .env
├── translation-service/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── translator.py
│   ├── Dockerfile
│   └── requirements.txt
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
├── test_services.sh
└── test_services.py
```

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Make sure you have the following installed:

-   [Docker](https://docs.docker.com/get-docker/)
-   [Docker Compose](https://docs.docker.com/compose/install/)
-   `curl` (for `test_services.sh`)
-   `jq` (for `test_services.sh` - a lightweight and flexible command-line JSON processor)
-   `python3` and `pip` (for `test_services.py`)
-   `npm` or `yarn` (for Node.js dependencies, though Docker handles this)

### Installation and Setup

1.  **Clone the repository (or create the project structure manually):**

    If you received this project as a zip file, extract it. Otherwise, if it was provided as a repository, clone it:

    ```bash
    git clone <repository-url>
    cd microservices-translation-project
    ```

2.  **Build and Run the Services:**

    Navigate to the root of the `microservices-translation-project` directory and run Docker Compose. This will build the Docker images, create the containers, and start all services (two databases, translation service, and product service).

    ```bash
    docker compose up --build -d
    ```

    The `-d` flag runs the containers in detached mode.

3.  **Verify Services are Running:**

    You can check the status of your running containers:

    ```bash
    docker compose ps
    ```

    You should see `product-service`, `translation-service`, `product-db`, and `translation-db` all in a healthy state.

    The Translation Microservice will download AI models on its first startup. This might take some time depending on your internet connection. You can monitor its logs:

    ```bash
    docker compose logs -f translation-service
    ```
    Look for messages like `Successfully loaded model for es` or `Model preloading complete`.

## Usage and Testing

Once all services are up and running, you can interact with them using `curl` or the provided test scripts.

### Service Endpoints

-   **Product Service**: `http://localhost:3000`
    -   `GET /docs`: Swagger UI documentation.
    -   `GET /products`: List all products.
    -   `GET /products/{product_id}`: Get a specific product.
    -   `POST /products`: Create a new product.
    -   `PUT /products/{product_id}`: Update a product.
    -   `DELETE /products/{product_id}`: Delete a product.
    -   `GET /health`: Health check.

-   **Translation Service**: `http://localhost:3001`
    -   `POST /translate`: Request translation for text.
    -   `GET /translations/{original_request_id}`: Get translations for a specific request ID.
    -   `GET /translations`: List all stored translations.
    -   `GET /health`: Health check.
    -   `GET /docs`: Swagger UI documentation.

### Running Tests

Two test scripts are provided:

1.  **`test_services.sh` (Bash script)**:

    This script uses `curl` and `jq` to perform a series of API calls to both services, demonstrating product creation, translation requests, and retrieval in different languages.

    ```bash
    ./test_services.sh
    ```

2.  **`test_services.py` (Python script)**:

    This script uses the `requests` library to perform similar tests, providing a more programmatic way to verify functionality.

    ```bash
    python3 test_services.py
    ```

    Both scripts will output the results of each step, including health checks, product creation, and translated product retrieval.

### Example Workflow (Manual `curl` commands)

1.  **Check Product Service Health:**

    ```bash
    curl http://localhost:3000/health
    ```

2.  **Check Translation Service Health:**

    ```bash
    curl http://localhost:3001/health
    ```

3.  **Create a Product (triggers translation):**

    ```bash
    curl -X POST http://localhost:3000/products \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Smart TV",
        "description": "4K HDR Smart TV with voice control",
        "price": 799.99,
        "auto_translate": true,
        "target_languages": ["es", "fr"]
      }'
    ```
    Note the `id` from the response.

4.  **Wait a few seconds for translations to process.**

5.  **Get the Product in Spanish:**

    ```bash
    curl http://localhost:3000/products/<PRODUCT_ID>?lang=es
    ```
    Replace `<PRODUCT_ID>` with the actual ID from step 3.

6.  **Get translations directly from the Translation Service:**

    ```bash
    curl http://localhost:3001/translations/<PRODUCT_ID>
    ```

## Shutting Down

To stop and remove all containers, networks, and volumes created by `docker-compose`:

```bash
docker compose down -v
```

The `-v` flag also removes the anonymous volumes, which include the database data and downloaded AI models. If you want to keep the database data and AI models for future runs, omit `-v`.

## Extending Supported Languages

To add more languages to the Translation Microservice:

1.  **Update `translation-service/app/translator.py`**: Add the new language code and its corresponding OPUS-MT model name to the `supported_languages` dictionary.
2.  **Rebuild `translation-service`**: Run `docker compose up --build -d translation-service` to rebuild the image with the updated code.
3.  The new model will be downloaded and loaded on the next startup of the `translation-service` container.

## Troubleshooting

-   **`Connection refused`**: Ensure all Docker containers are running and healthy (`docker compose ps`). Check container logs for errors (`docker compose logs <service-name>`).
-   **Translation issues**: Verify the Translation Microservice is healthy and its models are loaded. Check the logs for any errors during model loading or translation.
-   **Database issues**: Ensure the database containers are healthy. Check their logs for any connection or migration errors.

---

**Author**: Manus AI
**Date**: Oct 05, 2025
