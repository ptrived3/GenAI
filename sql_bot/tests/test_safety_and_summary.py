from sql_bot.main import handle_query

def test_safety_gate_blocks_non_select(monkeypatch):
    monkeypatch.setattr("sql_bot.main.generate_sql", lambda q: "DROP TABLE products")
    res = handle_query("be evil")
    assert "error" in res
    assert "single safe SELECT" in res["error"]

def test_summary_is_called(monkeypatch):
    monkeypatch.setattr(
        "sql_bot.main.generate_sql",
        lambda q: "SELECT name, price FROM products ORDER BY price DESC LIMIT 3"
    )
    monkeypatch.setattr("sql_bot.main.summarize", lambda q, rows: "SUMMARY_OK")
    out = handle_query("top 3 prices")
    assert out["summary"] == "SUMMARY_OK"
