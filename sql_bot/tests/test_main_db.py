import pandas as pd
from sqlalchemy import text
from sql_bot.main import handle_query

def test_products_over_15(monkeypatch):
    # stub LLM to known SQL (avoid OpenAI in tests)
    monkeypatch.setattr(
        "sql_bot.main.generate_sql",
        lambda q: "SELECT name, price FROM products WHERE price > 15 ORDER BY price ASC"
    )
    # stub summarizer
    monkeypatch.setattr("sql_bot.main.summarize", lambda q, rows: "ok")

    res = handle_query("List products > $15")
    assert "error" not in res
    df = res["table"]
    assert not df.empty
    assert list(df.columns) == ["name", "price"]
    assert (df["price"] > 15).all()

def test_total_revenue_top5(monkeypatch):
    monkeypatch.setattr(
        "sql_bot.main.generate_sql",
        lambda q: ("SELECT p.name, SUM(p.price*o.quantity) AS total_revenue "
                   "FROM products p JOIN orders o ON p.id=o.product_id "
                   "GROUP BY p.name ORDER BY total_revenue DESC LIMIT 5")
    )
    monkeypatch.setattr("sql_bot.main.summarize", lambda q, rows: "ok")

    res = handle_query("Top 5 by revenue")
    assert "error" not in res
    df = res["table"]
    assert not df.empty
    assert "total_revenue" in df.columns
    # revenues should be sorted desc
    assert df["total_revenue"].tolist() == sorted(df["total_revenue"].tolist(), reverse=True)
