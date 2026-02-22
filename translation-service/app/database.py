from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
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

def check_and_migrate_db(engine_instance, base_model=None):
    """
    Checks if the 'translations' table matches the new schema (separate name/description).
    If it detects the old schema (single text column), it drops the table
    to allow it to be recreated with the new schema.
    """
    logger.info("Checking database schema for migrations...")
    inspector = inspect(engine_instance)

    if not inspector.has_table("translations"):
        logger.info("Table 'translations' does not exist yet.")
        if base_model:
            logger.info("Creating table 'translations'...")
            base_model.metadata.create_all(bind=engine_instance)
        return

    columns = [col['name'] for col in inspector.get_columns("translations")]

    # Check for old schema
    if "original_text" in columns:
        logger.warning("Old schema detected (original_text column found). Dropping table 'translations' to reset schema...")
        with engine_instance.connect() as conn:
            conn.execute(text("DROP TABLE translations"))
            conn.commit()

        if base_model:
            logger.info("Recreating table 'translations' with new schema...")
            base_model.metadata.create_all(bind=engine_instance)
    else:
        logger.info("Schema appears correct (no 'original_text' column).")

    logger.info("Database schema check complete.")
