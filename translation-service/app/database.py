from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://translation_user:translation_pass@translation-db:5432/translations_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_migrations():
    """Run Alembic migrations to upgrade the database schema."""
    try:
        logger.info("Running database migrations...")
        # Assuming alembic.ini is in the current working directory or provided path
        # If run from root of translation-service, "alembic.ini" is correct.
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations complete.")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise e
