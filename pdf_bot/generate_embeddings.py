# generate_embeddings.py
import os
import numpy as np
from .pdf_utils import extract_text_from_pdf, chunk_text, add_metadata_to_chunks
from sklearn.metrics.pairwise import cosine_similarity
import ollama

OLLAMA_MODEL = "mxbai-embed-large"

def get_embeddings_from_folder(folder_path):
    all_documents = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            full_path = os.path.join(folder_path, filename)
            raw_text = extract_text_from_pdf(full_path)
            chunks = chunk_text(raw_text)
            documents = add_metadata_to_chunks(chunks, full_path)
            all_documents.extend(documents)

    texts = [doc["content"] for doc in all_documents]
    
    embeddings = []
    for text in texts:
        response = ollama.embeddings(model=OLLAMA_MODEL, prompt=text)
        embeddings.append(response["embedding"])

    embedded_documents = []
    for i, doc in enumerate(all_documents):
        embedded_documents.append({
            "embedding": embeddings[i],
            "metadata": doc["metadata"],
            "content": doc["content"]
        })

    return embedded_documents, None  # model is not needed with Ollama

def find_relevant_chunks(query, embedded_documents, model=None, k=4):
    response = ollama.embeddings(model=OLLAMA_MODEL, prompt=query)
    query_embedding = np.array(response["embedding"])
    
    doc_embeddings = [np.array(doc["embedding"]) for doc in embedded_documents]
    scores = cosine_similarity([query_embedding], doc_embeddings)[0]
    
    top_k = sorted(zip(scores, embedded_documents), reverse=True)[:k]
    return [doc for _, doc in top_k]