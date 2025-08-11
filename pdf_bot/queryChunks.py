# queryChunks.py

import os, psycopg2, ollama, numpy as np
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


def connect_db():
    return psycopg2.connect(
        dbname=os.getenv("LLM_SQL_DBNAME", "llm_sql_demo"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost")
    )


def get_top_k_chunks(query, k=3, model_name="mxbai-embed-large"):
    conn = connect_db()
    cur = conn.cursor()

    # 1. Embed query
    response = ollama.embeddings(model=model_name, prompt=query)
    query_embedding = response["embedding"]

    # 2. Convert to Postgres array format
    embedding_str = "[" + ",".join([str(x) for x in query_embedding]) + "]"

    # 3. Retrieve top-k with similarity score
    cur.execute(f"""
        SELECT content, metadata, embedding <-> %s AS score
        FROM document_chunks
        ORDER BY score ASC
        LIMIT %s
    """, (embedding_str, k))

    results = cur.fetchall()
    conn.close()
    return results  # (content, metadata, score)
