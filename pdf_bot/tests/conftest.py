# pdf_bot/tests/conftest.py
import os, pathlib, psycopg2, pytest
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema.sql"

def _conn():
    return psycopg2.connect(
        dbname=os.getenv("LLM_SQL_DBNAME", "llm_sql_demo"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
    )

@pytest.fixture(scope="session", autouse=True)
def setup_schema():
    with _conn() as c, c.cursor() as cur:
        cur.execute(open(SCHEMA, "r").read())
        c.commit()

@pytest.fixture(autouse=True)
def seed_minimal():
    with _conn() as c, c.cursor() as cur:
        cur.execute("TRUNCATE order_items, orders, products RESTART IDENTITY CASCADE;")
        cur.execute("INSERT INTO products (name, price) VALUES ('Widget',9.99),('Gadget',19.50),('Doodad',5.25);")
        cur.execute("INSERT INTO orders (customer, order_date) VALUES ('Alice','2024-03-10'), ('Bob','2024-03-11');")
        cur.execute("INSERT INTO order_items (order_id, product_id, quantity) VALUES (1,1,2),(1,2,1);")
        c.commit()
    yield
    with _conn() as c, c.cursor() as cur:
        cur.execute("TRUNCATE order_items, orders, products RESTART IDENTITY CASCADE;")
        c.commit()
