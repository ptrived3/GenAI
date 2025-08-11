from sql_bot.main import handle_query
from sqlalchemy import text
from sql_bot.database import SessionLocal

def test_web_fallback_inserts_and_returns(monkeypatch):
    # 1) First LLM SQL yields no rows (forces fallback)
    monkeypatch.setattr(
        "sql_bot.main.generate_sql",
        lambda q: "SELECT answer FROM web_facts WHERE question ILIKE '%{q}%'".format(q=q.replace("'", "''"))
    )
    # 2) Summarizer stub
    monkeypatch.setattr("sql_bot.main.summarize", lambda q, rows: "ok")
    # 3) Web fetcher stub (no network)
    monkeypatch.setattr(
        "sql_bot.main.answer_from_web",
        lambda q: ("1", "https://solarsystem.nasa.gov/moons/earths-moon/overview/")
    )

    res = handle_query("How many moons does Earth have?")
    assert "error" not in res
    df = res["table"]
    # thanks to safety-net, we should still see an answer even if LLM SQL is imperfect
    assert not df.empty
    # either column may be 'answer' or an alias from LLM; check presence
    assert any(col.lower() in ("answer", "earth_moons") for col in df.columns)
    # and ensure it got saved
    with SessionLocal() as s:
        count = s.execute(text("SELECT COUNT(*) FROM web_facts")).scalar()
    assert count == 1
