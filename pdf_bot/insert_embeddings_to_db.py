# insert_embeddings_to_db.py
import os, json, psycopg2, ollama
from dotenv import load_dotenv, find_dotenv
from .pdf_utils import extract_text_from_pdf, chunk_text, add_metadata_to_chunks

load_dotenv(find_dotenv())

# PG connection
def connect_db():
    return psycopg2.connect(
        dbname=os.getenv("LLM_SQL_DBNAME", "llm_sql_demo"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost")
    )


def insert_document_chunk(conn, content, metadata, embedding):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO document_chunks (content, metadata, embedding)
            VALUES (%s, %s, %s)
        """, (content, json.dumps(metadata), embedding))
    conn.commit()

# Main ETL
def embed_and_store_pdfs(folder_path, model_name="mxbai-embed-large"):
    conn = connect_db()
    all_documents = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            full_path = os.path.join(folder_path, filename)
            raw_text = extract_text_from_pdf(full_path)
            chunks = chunk_text(raw_text)
            documents = add_metadata_to_chunks(chunks, full_path)
            all_documents.extend(documents)

    for doc in all_documents:
        content = doc["content"]
        metadata = doc["metadata"]
        response = ollama.embeddings(model=model_name, prompt=content)
        embedding = response["embedding"]
        insert_document_chunk(conn, content, metadata, embedding)

    conn.close()
    print(f"Inserted {len(all_documents)} chunks into PostgreSQL!")


    # insert_embeddings_to_db.py  (append at bottom)

def embed_and_store_pdf(pdf_path, model_name="mxbai-embed-large"):
    """
    Extracts, chunks, embeds and inserts ONE PDF into your document_chunks table.
    """
    conn = connect_db()
    # extract & chunk
    raw_text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(raw_text)
    documents = add_metadata_to_chunks(chunks, pdf_path)
    # embed & insert
    for doc in documents:
        content, metadata = doc["content"], doc["metadata"]
        resp = ollama.embeddings(model=model_name, prompt=content)
        embedding = resp["embedding"]
        insert_document_chunk(conn, content, metadata, embedding)
    conn.close()


# Run it
if __name__ == "__main__":
    embed_and_store_pdfs("pdfs")  # Make sure your PDFs are in this folder
