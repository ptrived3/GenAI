# pdf_utils.py

import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path

def extract_text_from_pdf(file_path):
    """Extract text from each page in a PDF."""
    doc = fitz.open(file_path)
    text = ""
    for i, page in enumerate(doc):
        text += f"\n--- Page {i+1} ---\n"
        text += page.get_text()
    doc.close()
    return text

def chunk_text(text, chunk_size=300, chunk_overlap=50):
    """Split text into overlapping chunks for processing."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(text)

def add_metadata_to_chunks(chunks, source_path):
    """Attach source file name and chunk index as metadata."""
    filename = Path(source_path).name
    return [
        {
            "content": chunk,
            "metadata": {
                "source": filename,
                "chunk_index": idx
            }
        }
        for idx, chunk in enumerate(chunks)
    ]

