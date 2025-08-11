# sql_bot/tests/conftest.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))  # ensure project root on path early

import os
import pytest
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import text
from sql_bot.database import engine

load_dotenv(find_dotenv())  # ensure DATABASE_URL is loaded

SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[1] / "sqlbot_schema.sql"

SEED_SQL = """
TRUNCATE orders RESTART IDENTITY CASCADE;
TRUNCATE products RESTART IDENTITY CASCADE;

INSERT INTO products (name, price) VALUES
  ('Widget',      9.99),
  ('Gadget',     19.50),
  ('Doodad',      5.25),
  ('Thingamajig',14.75),
  ('Contraption',49.00),
  ('Whatsit',     2.99),
  ('Gizmo',      29.99),
  ('Bolt Pack',   3.49),
  ('Sprocket',   12.25),
  ('MegaWidget', 24.95);

INSERT INTO orders (product_id, quantity, order_date) VALUES
  (1,  3, '2024-01-15'),
  (2,  1, '2024-02-10'),
  (3, 10, '2024-03-05'),
  (1,  2, '2024-03-17'),
  (4,  4, '2024-04-02'),
  (5,  1, '2024-04-18'),
  (6, 12, '2024-05-01'),
  (7,  2, '2024-05-12'),
  (8, 25, '2024-05-20'),
  (9,  6, '2024-06-03'),
  (10, 3, '2024-06-15'),
  (2,  5, '2024-06-28'),
  (3,  7, '2024-07-04'),
  (4,  1, '2024-07-09'),
  (5,  2, '2024-07-11'),
  (6, 20, '2024-07-22'),
  (7,  1, '2024-08-01'),
  (8, 30, '2024-08-02'),
  (9,  2, '2024-08-03'),
  (10, 5, '2024-08-04');
"""

WEB_FACTS_SQL = """
CREATE TABLE IF NOT EXISTS web_facts (
  id SERIAL PRIMARY KEY,
  question   TEXT NOT NULL,
  answer     TEXT NOT NULL,
  source_url TEXT NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

def _exec_multi(conn, sql_blob: str):
    # naive splitter good enough for our simple schema/seed
    for stmt in [s.strip() for s in sql_blob.split(";") if s.strip()]:
        conn.execute(text(stmt))

@pytest.fixture(scope="session", autouse=True)
def setup_schema():
    with engine.begin() as conn:
        # core schema
        with open(SCHEMA_PATH, "r") as f:
            _exec_multi(conn, f.read())
        # web_facts table
        _exec_multi(conn, WEB_FACTS_SQL)
        # add extension/index AFTER table exists (and ignore if not allowed)
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        except Exception:
            pass
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS web_facts_question_trgm_idx
                ON web_facts USING gin (question gin_trgm_ops)
            """))
        except Exception:
            # fallback btree index if trigram not available
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS web_facts_question_idx ON web_facts (question)"))
            except Exception:
                pass
    yield

@pytest.fixture(autouse=True)
def seed_db(setup_schema):
    with engine.begin() as conn:
        _exec_multi(conn, SEED_SQL)
        conn.execute(text("TRUNCATE web_facts RESTART IDENTITY"))
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE web_facts RESTART IDENTITY"))
