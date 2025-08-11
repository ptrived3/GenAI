# sql_bot/main.py
import re
import pandas as pd
from sqlalchemy import text

from .nlp_to_sql import generate_sql
from .summarizer import summarize
from .database import SessionLocal
from .web_qa import answer_from_web


def _cleanup_sql(raw_sql: str) -> str:
    m = re.search(r'```(?:sql)?\s*([\s\S]*?)```', raw_sql, re.IGNORECASE)
    sql = (m.group(1) if m else raw_sql).strip()
    sql = re.sub(r'\s+', ' ', sql).strip()
    return sql[:-1] if sql.endswith(';') else sql


def _is_safe_select(sql: str) -> bool:
    if not re.match(r'^\s*select\b', sql, flags=re.IGNORECASE):
        return False
    if ';' in sql:
        return False
    banned = r'\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|commit|rollback)\b'
    return re.search(banned, sql, flags=re.IGNORECASE) is None


def handle_query(question: str):
    # 1) LLM → SQL
    raw_sql = generate_sql(question)
    clean_sql = _cleanup_sql(raw_sql)
    if not _is_safe_select(clean_sql):
        return {"error": "Generated SQL was not a single safe SELECT.", "sql": clean_sql}

    session = SessionLocal()
    df = pd.DataFrame()
    try:
        # 2) Try DB first
        result = session.execute(text(clean_sql))
        rows = result.fetchall()
        cols = result.keys()
        df = pd.DataFrame(rows, columns=cols)

        if df.empty:
            # 2a) Web fallback
            ans, src = answer_from_web(question)
            if ans and src:
                session.execute(
                    text("INSERT INTO web_facts (question, answer, source_url) VALUES (:q, :a, :u)"),
                    {"q": question, "a": ans, "u": src}
                )
                session.commit()

                # 2b) Re-run LLM SQL now that web_facts has data
                raw_sql2 = generate_sql(question)
                clean_sql2 = _cleanup_sql(raw_sql2)
                if _is_safe_select(clean_sql2):
                    result2 = session.execute(text(clean_sql2))
                    rows2 = result2.fetchall()
                    cols2 = result2.keys()
                    df = pd.DataFrame(rows2, columns=cols2)
                    clean_sql = clean_sql2  # show the SQL that produced rows

                # 2c) Safety net: if still empty, do robust direct select or return scraped
                if df.empty:
                    result3 = session.execute(text("""
                        SELECT answer, source_url, fetched_at
                        FROM web_facts
                        WHERE question ILIKE :q
                        ORDER BY fetched_at DESC
                        LIMIT 1
                    """), {"q": f"%{question}%"})
                    rows3 = result3.fetchall()
                    if rows3:
                        df = pd.DataFrame(rows3, columns=["answer", "source_url", "fetched_at"])
                    else:
                        df = pd.DataFrame([{"answer": ans, "source_url": src}])
                
                # if "web_facts" in clean_sql.lower() and "source_url" not in [c.lower() for c in df.columns]:
                #     with SessionLocal() as s:
                #         r = s.execute(text("""
                #             SELECT answer, source_url, fetched_at
                #             FROM web_facts
                #             WHERE question ILIKE :q
                #             ORDER BY fetched_at DESC
                #             LIMIT 1
                #         """), {"q": f"%{question}%"}).fetchone()
                #         if r:
                #             # append source_url column if missing
                #             if "source_url" not in df.columns:
                #                 df["source_url"] = r.source_url
                
                cols_lower = {c.lower() for c in df.columns}
                if ("answer" in cols_lower) and ("source_url" not in cols_lower):
                    with SessionLocal() as s:
                        r = (
                            s.execute(
                                text("""
                                    SELECT answer, source_url, fetched_at
                                    FROM web_facts
                                    WHERE question ILIKE :q
                                    ORDER BY fetched_at DESC
                                    LIMIT 1
                                """),
                                {"q": f"%{question}%"},
                            )
                            .mappings()
                            .first()
                        )
                        if r and r.get("source_url"):
                            # broadcast the latest source_url to the current df
                            df["source_url"] = r["source_url"]

    except Exception as e:
        return {"error": str(e), "sql": clean_sql}
    finally:
        session.close()

    # 3) Summarize
    summary = summarize(question, df.to_dict(orient="records"))
    return {"table": df, "summary": summary, "sql": clean_sql}

# # sql_bot/main.py
# import re
# import pandas as pd

# from .nlp_to_sql import generate_sql
# from .summarizer import summarize
# from .database import SessionLocal
# from sqlalchemy import text

# from .database import SessionLocal
# from .web_qa import answer_from_web


# def _cleanup_sql(raw_sql: str) -> str:
#     """
#     Strip optional ```sql ... ``` fences, collapse whitespace, and remove a trailing semicolon.
#     """
#     m = re.search(r'```(?:sql)?\s*([\s\S]*?)```', raw_sql, re.IGNORECASE)
#     sql = (m.group(1) if m else raw_sql).strip()
#     # Collapse internal whitespace to single spaces to avoid odd formatting issues
#     sql = re.sub(r'\s+', ' ', sql).strip()
#     # Drop trailing semicolon (we disallow multi-statement anyway)
#     sql = sql[:-1] if sql.endswith(';') else sql
#     return sql


# def _is_safe_select(sql: str) -> bool:
#     """
#     Allow exactly one statement that starts with SELECT and contains no DDL/DML keywords.
#     """
#     # must start with SELECT
#     if not re.match(r'^\s*select\b', sql, flags=re.IGNORECASE):
#         return False
#     # disallow semicolons to avoid multiple statements
#     if ';' in sql:
#         return False
#     # block dangerous keywords
#     banned = r'\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|commit|rollback)\b'
#     if re.search(banned, sql, flags=re.IGNORECASE):
#         return False
#     return True


# def handle_query(question: str):
#     raw_sql = generate_sql(question)
#     clean_sql = _cleanup_sql(raw_sql)

#     if not _is_safe_select(clean_sql):
#         return {"error": "Generated SQL was not a single safe SELECT.", "sql": clean_sql}

#     session = SessionLocal()
#     try:
#         result = session.execute(text(clean_sql))
#         rows = result.fetchall()
#         cols = result.keys()
#         df = pd.DataFrame(rows, columns=cols)

#         # If DB has nothing useful, try web fallback
#         if df.empty:
#             # Try to answer from the web:
#             ans, src = answer_from_web(question)
#             if ans and src:
#                 # Store into web_facts so NL→SQL can query it next time
#                 session.execute(
#                     text("INSERT INTO web_facts (question, answer, source_url) VALUES (:q, :a, :u)"),
#                     {"q": question, "a": ans, "u": src}
#                 )
#                 session.commit()
#                 # Re-ask the LLM for SQL now that web_facts has data
#                 raw_sql2 = generate_sql(question)
#                 clean_sql2 = _cleanup_sql(raw_sql2)
#                 if _is_safe_select(clean_sql2):
#                     result2 = session.execute(text(clean_sql2))
#                     rows2 = result2.fetchall()
#                     cols2 = result2.keys()
#                     df = pd.DataFrame(rows2, columns=cols2)
#                     clean_sql = clean_sql2  # update to the SQL that returned rows
        
#         # after generating clean_sql2 and possibly setting df from result2
#         if df.empty:
#             # Try a robust direct lookup in web_facts
#             result3 = session.execute(text("""
#                 SELECT answer, source_url, fetched_at
#                 FROM web_facts
#                 WHERE question ILIKE :q
#                 ORDER BY fetched_at DESC
#                 LIMIT 1
#             """), {"q": f"%{question}%"})
#             rows3 = result3.fetchall()
#             if rows3:
#                 df = pd.DataFrame(rows3, columns=["answer", "source_url", "fetched_at"])
#             else:
#                 # ultimate fallback: return the scraped answer directly
#                 # (this path only happens if insert failed unexpectedly)
#                 df = pd.DataFrame([{"answer": ans, "source_url": src}])


#     except Exception as e:
#         session.close()
#         return {"error": str(e), "sql": clean_sql}
#     finally:
#         session.close()

#     summary = summarize(question, df.to_dict(orient="records"))
#     return {"table": df, "summary": summary, "sql": clean_sql}



#     """
#     1) Turn the question into SQL
#     2) Run it against Postgres
#     3) Summarize the results

#     Returns a dict with keys:
#       - "table": pandas DataFrame of results
#       - "summary": human-readable summary
#       - "sql": the generated SQL string (cleaned)
#       - "error": present only when something failed
#     """
#     # 1) LLM → SQL
#     raw_sql = generate_sql(question)
#     clean_sql = _cleanup_sql(raw_sql)

#     # Safety gate
#     if not _is_safe_select(clean_sql):
#         return {"error": "Generated SQL was not a single safe SELECT.", "sql": clean_sql}

#     # 2) Execute on Postgres
#     session = SessionLocal()
#     try:
#         result = session.execute(text(clean_sql))
#         rows = result.fetchall()
#         cols = result.keys()
#         df = pd.DataFrame(rows, columns=cols)
#     except Exception as e:
#         return {"error": str(e), "sql": clean_sql}
#     finally:
#         session.close()

#     # 3) Summarize
#     summary = summarize(question, df.to_dict(orient="records"))

#     return {"table": df, "summary": summary, "sql": clean_sql}
