from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import os
import logging

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

def check_and_migrate_db():
    """
    Check for missing columns and add them if necessary.
    This is a simple migration strategy for this microservice.
    """
    try:
        inspector = inspect(engine)
        if not inspector.has_table("translations"):
            logger.info("Table 'translations' does not exist yet. Skipping migration.")
            return

        columns = [col['name'] for col in inspector.get_columns("translations")]

        with engine.connect() as conn:
            with conn.begin():
                if "confidence_score" not in columns:
                    logger.info("Adding column 'confidence_score' to translations table")
                    conn.execute(text("ALTER TABLE translations ADD COLUMN confidence_score FLOAT"))

                if "back_translation" not in columns:
                    logger.info("Adding column 'back_translation' to translations table")
                    conn.execute(text("ALTER TABLE translations ADD COLUMN back_translation TEXT"))

                if "needs_review" not in columns:
                    logger.info("Adding column 'needs_review' to translations table")
                    conn.execute(text("ALTER TABLE translations ADD COLUMN needs_review BOOLEAN DEFAULT FALSE"))

        logger.info("Database migration check complete")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        # Don't raise here to allow startup to continue if DB is not ready,
        # though functionality might be impaired.
