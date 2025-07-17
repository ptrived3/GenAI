# queryChunks.py

import psycopg2
import ollama
import numpy as np

def connect_db():
    return psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost"
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
