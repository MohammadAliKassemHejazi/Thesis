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

def check_and_migrate_db(engine_instance):
    """
    Checks if required columns exist in the 'translations' table
    and adds them if they are missing.
    """
    logger.info("Checking database schema for migrations...")
    inspector = inspect(engine_instance)

    if not inspector.has_table("translations"):
        logger.info("Table 'translations' does not exist yet. It will be created by Base.metadata.create_all()")
        return

    columns = [col['name'] for col in inspector.get_columns("translations")]

    with engine_instance.connect() as conn:
        # Check and add 'field_name' column
        if "field_name" not in columns:
            logger.info("Adding missing column: field_name")
            conn.execute(text("ALTER TABLE translations ADD COLUMN field_name VARCHAR(50)"))
            conn.commit()

        # Check and add 'is_edited' column
        if "is_edited" not in columns:
            logger.info("Adding missing column: is_edited")
            conn.execute(text("ALTER TABLE translations ADD COLUMN is_edited BOOLEAN DEFAULT FALSE"))
            conn.commit()

        # Check and add 'edited_text' column
        if "edited_text" not in columns:
            logger.info("Adding missing column: edited_text")
            conn.execute(text("ALTER TABLE translations ADD COLUMN edited_text TEXT"))
            conn.commit()

        # Check and add 'feedback' column
        if "feedback" not in columns:
            logger.info("Adding missing column: feedback")
            conn.execute(text("ALTER TABLE translations ADD COLUMN feedback TEXT"))
            conn.commit()

    logger.info("Database schema check complete.")
