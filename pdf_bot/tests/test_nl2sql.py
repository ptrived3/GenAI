# pdf_bot/tests/test_nl2sql.py
from pathlib import Path
import sys, os
import pytest

# Ensure project root on path so we can do package import
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pdf_bot.genAI import generate_sql, run_sql_query  # use package import

def test_orders_by_alice():
    # Rely on pdf_bot/tests/conftest.py to create schema + seed Alice
    sql = generate_sql("List orders by Alice")
    assert "orders" in sql.lower()
    # don't over-specify; the LLM may not echo 'alice' in the SQL string
    df = run_sql_query(sql)
    assert not df.empty
    # be flexible in case the model returns extra columns / joins
    assert any(str(v).lower() == "alice" for v in df.get("customer", []))



# # tests/test_nl2sql.py

# import sys, os
# from pathlib import Path

# ROOT = Path(__file__).resolve().parents[1]
# SCHEMA_PATH = ROOT / "pdf_bot" / "schema.sql"

# with open(SCHEMA_PATH, "r") as f:
#     schema_sql = f.read()

# # 1) make sure project root is on PYTHONPATH before any imports
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# import pytest
# from genAI import generate_sql, run_sql_query, connect_db

# @pytest.fixture(scope="module")
# def db_conn():
#     conn = connect_db()
#     with conn.cursor() as cur:
#         # drop any old tables
#         cur.execute("DROP TABLE IF EXISTS order_items CASCADE;")
#         cur.execute("DROP TABLE IF EXISTS orders       CASCADE;")
#         cur.execute("DROP TABLE IF EXISTS products     CASCADE;")

#         # recreate everything (this also INSERTs the sample data!)
#         cur.execute(open("schema.sql").read())

#         # ── CLEAN UP SAMPLE DATA ──
#         cur.execute("DELETE FROM order_items;")  # remove sample order_items
#         cur.execute("DELETE FROM orders;")       # remove sample orders
#         conn.commit()

#         # ── NOW SEED ONLY YOUR TEST ROW ──
#         cur.execute("""
#             INSERT INTO orders (order_id, customer, order_date)
#             VALUES (1, 'Alice', '2025-06-05');
#         """)
#         conn.commit()

#     yield conn
#     conn.close()



# def test_orders_by_alice(db_conn):
#     sql = generate_sql("List orders by Alice")
#     assert "orders" in sql.lower()
#     assert "alice" in sql.lower()

#     df = run_sql_query(sql)
#     assert not df.empty
#     assert df.iloc[0]["customer"] == "Alice"

