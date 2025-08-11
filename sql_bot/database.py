# sql_bot/database.py
import os
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load env
load_dotenv(find_dotenv())

# Build engine/session
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def bootstrap_indexes():
    """Create helpful extensions/indexes if possible."""
    with engine.begin() as conn:
        # Try fast trigram search first; if extension/table not present, fall back quietly
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS web_facts_question_trgm_idx
                ON web_facts USING gin (question gin_trgm_ops)
            """))
        except Exception:
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS web_facts_question_idx
                    ON web_facts (question)
                """))
            except Exception:
                pass

# If you want this to run automatically on import, uncomment:
# try:
#     bootstrap_indexes()
# except Exception:
#     pass
