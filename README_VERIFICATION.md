# Verification Report: Provided Text vs Actual Codebase

This document outlines the differences between the provided text specification and the actual project codebase. It only lists what does not match.

## Mismatches Found

### 1.1 Project Structure
*   **Text says:** `server.js` and `package.json` are at the root of `product-service/`.
*   **Actual project:** `server.js` is inside `product-service/src/server.js`.

### 1.2 Application Entry Point (`src/app.js`)
*   **Text says:** Uses `require('./config/swagger.json')`. Routes like `/health` and `/` are defined directly in `app.js`.
*   **Actual project:** Uses `require('./config/swagger')` (which resolves to `swagger.js`). Routes are handled by dedicated routers (`healthRoutes.js`, `productRoutes.js`) instead of being inline. It also includes middleware like `cors`, `bodyParser`, and request logging that are not mentioned in the text.

### 1.3 Sequelize Database Configuration (`src/config/database.js`)
*   **Text says:** The file is named `database.js` and defaults to `postgres` for user/password/DB.
*   **Actual project:** The file is named `sequelize.js`. It defaults to `products_db`, `product_user`, and `product_pass`.

### 1.4 Product Model (`src/models/product.model.js`)
*   **Text says:** File is named `product.model.js`. `name` field is `DataTypes.STRING`. `price` is `DataTypes.DECIMAL(10,2)`.
*   **Actual project:** File is named `Product.js`. `name` field is `DataTypes.STRING(255)`.

### 1.5 Product Creation with Async Translation (`src/services/product.service.js`)
*   **Text says:** File is named `product.service.js`. `axios.post` is called directly inside `createProduct` and uses `const TRANS = process.env.TRANSLATION_SERVICE_URL`.
*   **Actual project:** File is named `productService.js`. The translation logic is extracted to a separate file `translationService.js` using a helper function `requestTranslation`. `ProductService` is implemented as a class.

### 1.6 Product Deletion with Synchronous Cleanup
*   **Text says:** `deleteProduct` does `await axios.delete(...)` directly.
*   **Actual project:** `deleteProduct` calls `await deleteTranslations(id)` which delegates the HTTP request to `translationService.js`.

### 2.1 Project Structure
*   **Text says:** `models.py`, `database.py`, `translator.py`, `main.py` are at the root of `translation-service/`.
*   **Actual project:** These files are located inside `translation-service/app/`.

### 2.2 FastAPI Entry Point (`app/main.py`)
*   **Text says:** Uses `@asynccontextmanager async def lifespan(app: FastAPI):` and `command.upgrade(alembic_cfg, "head")` for migrations and loads OPUS-MT models using `load_all_models()`.
*   **Actual project:** Uses `@app.on_event("startup")`. Does not use Alembic `command.upgrade`, instead uses `Base.metadata.create_all(bind=engine)`. Calls `translation_engine.preload_all_models()`.

### 2.3 Model Loader and Translator (`app/translator.py`)
*   **Text says:** Defines `MODELS: dict` and `def load_all_models()` and `def translate_text(text: str, target_lang: str) -> str:`.
*   **Actual project:** Defines a `TranslationEngine` class with `load_model`, `translate`, and `preload_all_models` methods, then exports an instance `translation_engine`.

### 2.4 Translation Pipeline Service (`app/services/translation_service.py`)
*   **Text says:** `db.query(Translation).filter(Translation.original_request_id == request.original_request_id, Translation.language == target_lang).first()` and handles `db.delete(existing)` and `db.add(translation)` with one `db.commit()` at the end of the loop iteration. The response returns translations list.
*   **Actual project:** Wraps the entire loop body in a `try...except` block and calls `db.rollback()` on error. The core translation logic functions essentially the same.

### 2.5 SQLAlchemy Translation Model (`app/models.py`)
*   **Text says:** `language` is `Column(String(10))`. `edited_name` is `Column(String)`. `created_at` is `Column(DateTime(timezone=True), server_default=func.now())`.
*   **Actual project:** `edited_name` is `Column(Text)`. `created_at` is `Column(DateTime, default=datetime.utcnow)`.

### 2.6 POST /translate Endpoint
*   **Text says:** Uses `app.api.v1.endpoints.translations`. Endpoint returns `translations` directly.
*   **Actual project:** Correct. The endpoint matches functionality using `translation_service.translate_content`.

### 2.7 Statistics Endpoint
*   **Text says:** Defined inline in `app.api.v1.endpoints.translations`.
*   **Actual project:** The logic is abstracted into `app.crud.translation.get_statistics` and the endpoint calls `get_statistics(db)`.

### 2.8 Dashboard Route
*   **Text says:** Located in `app/api/v1/endpoints/translations.py`. Uses `Jinja2Templates` and queries `db.query(Translation)`.
*   **Actual project:** Located in `app/main.py`. Does not use `Jinja2Templates`. It simply reads the static HTML file `Path("app/templates/dashboard.html").read_text()`.

### 3.1 Products Database Schema
*   **Text says:** Explicit `init.sql` file creates tables and triggers for `updated_at`.
*   **Actual project:** There is no `init.sql`. The schema is generated by Sequelize calling `sequelize.sync()`.

### 3.2 Translations Database Schema
*   **Text says:** `alembic/versions/initial_migration.py` contains raw SQL like `CREATE TABLE translations (...)`.
*   **Actual project:** No raw SQL migration is used. Schema is generated by SQLAlchemy `Base.metadata.create_all(bind=engine)`.

### 4.1 Product Service Dockerfile
*   **Text says:** `node:18-alpine` and `npm ci --omit=dev`.
*   **Actual project:** Uses `node:22-alpine` and `npm install --production`.

### 4.2 Translation Service Dockerfile
*   **Text says:** `python:3.10-slim`.
*   **Actual project:** Uses `python:3.11-slim`. Also installs `postgresql-client` and `libpq-dev`, and runs a custom `download_models.py` script.

### 4.3 Docker Compose Configuration
*   **Text says:** DB credentials use user `postgres` and pass `postgres`. `translation-db` uses port `5433:5432`.
*   **Actual project:** DB credentials use `product_user`/`product_pass` and `translation_user`/`translation_pass`. Ports match. `DATABASE_URL` uses the correct user credentials.

## What Matches the Project Correctly

The core architecture, the endpoint paths (like `/translate`, `/products`), the database technologies (Postgres + Sequelize / SQLAlchemy), and the async fire-and-forget mechanism between the Node.js service and the Python service all function as described in the text. The synchronous deletion protocol is also correctly followed in the project code.
