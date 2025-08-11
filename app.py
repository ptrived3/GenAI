import os
import time
import streamlit as st
import pathlib
import pandas as pd

from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from openai import OpenAI
import ollama
from concurrent.futures import ThreadPoolExecutor, as_completed

from sql_bot.main import handle_query as handle_sql

from pdf_bot.pdf_utils import extract_text_from_pdf, chunk_text, add_metadata_to_chunks
from pdf_bot.insert_embeddings_to_db import connect_db, insert_document_chunk
from pdf_bot.genAI import send_pdf_answer


# ─── Set up your PDF directory ─────────────────────────────────────────────
# Figure out where “pdf_bot/pdfs” really lives on disk:
BASE_DIR = pathlib.Path(__file__).parent.resolve()      # …/OpenAI
PDF_DIR  = BASE_DIR / "pdf_bot" / "pdfs"
PDF_DIR.mkdir(exist_ok=True)


# ─── Config & Initialization ──────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OLLAMA_MODEL = "mxbai-embed-large"

os.makedirs("pdfs", exist_ok=True)

os.makedirs(str(PDF_DIR), exist_ok=True)

st.set_page_config(page_title="PDF Chatbot with Sessions", layout="centered")
st.title("PDF Chatbot")

st.sidebar.title("Mode")
mode = st.sidebar.radio("Choose mode", ["PDF Chatbot", "SQL Bot"])


# --- SQL Bot (chat UI) ----------------------------------------------------
if mode == "SQL Bot":
    st.header("🔍 SQL Bot")

    # chat history just for SQL bot
    if "sql_chat" not in st.session_state:
        st.session_state.sql_chat = []

    # toolbar
    left, right = st.columns([1, 1])
    with left:
        if st.button("➕ New SQL chat"):
            st.session_state.sql_chat = []
            st.rerun()
    with right:
        st.caption(f"{len(st.session_state.sql_chat)//2} turns")

    # render prior turns
    for i, msg in enumerate(st.session_state.sql_chat):
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                # assistant turn: summary + (optional) SQL + table + CSV
                st.markdown(msg["summary"])
                if msg.get("sql"):
                    with st.expander("Generated SQL", expanded=True):
                        st.code(msg["sql"], language="sql")
                if msg.get("table_records"):
                    df_hist = pd.DataFrame(msg["table_records"])
                    st.dataframe(df_hist, use_container_width=True)
                    csv_hist = df_hist.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download CSV",
                        csv_hist,
                        file_name=f"sql_result_{i}.csv",
                        mime="text/csv",
                        key=f"csv_{i}",
                    )

    # chat input
    user_q = st.chat_input("Ask a question about your database…")
    if user_q:
        # echo user
        st.session_state.sql_chat.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.markdown(user_q)

        # run pipeline -> show results
        with st.chat_message("assistant"):
            with st.spinner("Generating SQL and running the query…"):
                resp = handle_sql(user_q)

            if "error" in resp:
                st.error(resp["error"])
                if resp.get("sql"):
                    with st.expander("Generated SQL", expanded=True):
                        st.code(resp["sql"], language="sql")
                # store assistant turn (no table)
                st.session_state.sql_chat.append({
                    "role": "assistant",
                    "summary": f"⚠️ {resp['error']}",
                    "sql": resp.get("sql", ""),
                })
            else:
                df = resp["table"]
                st.markdown(resp["summary"])

                with st.expander("Generated SQL", expanded=True):
                    st.code(resp["sql"], language="sql")

                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download results as CSV",
                    csv,
                    file_name="query_results.csv",
                    mime="text/csv",
                )

                # store assistant turn (persist table as records for replay)
                st.session_state.sql_chat.append({
                    "role": "assistant",
                    "summary": resp["summary"],
                    "sql": resp["sql"],
                    "table_records": df.to_dict(orient="records"),
                })

    st.stop()

# ─── Session State: Multiple Chat Sessions ─────────────────────────────────
if "chat_sessions" not in st.session_state:
    # Initialize with one session
    st.session_state.chat_sessions = {"Chat 1": []}
    st.session_state.current_chat = "Chat 1"
if "processed_uploads" not in st.session_state:
    st.session_state.processed_uploads = set()
if "processed_dragged" not in st.session_state:
    st.session_state.processed_dragged = set()
if "summaries" not in st.session_state:
    st.session_state.summaries = {}


# ─── Sidebar: Chat Sessions + PDF Index ────────────────────────────────────
st.sidebar.header("Chats")
if st.sidebar.button("New Chat"):
    # create & switch to a fresh session
    idx = len(st.session_state.chat_sessions) + 1
    name = f"Chat {idx}"
    st.session_state.chat_sessions[name] = []
    st.session_state.current_chat = name
    st.rerun()


# Dropdown to select existing chat
chat_list = list(st.session_state.chat_sessions.keys())
st.session_state.current_chat = st.sidebar.selectbox(
    "Select Chat", chat_list,
    index=chat_list.index(st.session_state.current_chat)
)


# st.sidebar.text(f"Looking in: {PDF_DIR}")
# st.sidebar.text(f"Found: {list(PDF_DIR.iterdir())}")

st.sidebar.header("Indexed PDFs")
pdf_list = sorted(os.listdir(PDF_DIR))
if pdf_list:
    for fname in pdf_list:
        cols = st.sidebar.columns([0.8, 0.2])
        cols[0].write(f"• {fname}")
        if cols[1].button("🗑️", key=f"del_{fname}"):
            os.remove(os.path.join(PDF_DIR, fname))
            st.session_state.processed_uploads.discard(fname)
            st.session_state.processed_dragged.discard(fname)
            st.sidebar.success(f"Deleted {fname}")
            st.rerun()

        
else:
    st.sidebar.write("_(No PDFs indexed yet)_")

# ─── PDF Processing Helper ─────────────────────────────────────────────────
def process_pdf_in_parallel(pdf_path: str) -> str:
    raw_text = extract_text_from_pdf(pdf_path)
    docs = add_metadata_to_chunks(chunk_text(raw_text), pdf_path)
    progress = st.sidebar.progress(0)
    total = len(docs)
    embeddings = [None] * total
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(ollama.embeddings,
                            model=OLLAMA_MODEL,
                            prompt=doc["content"]): idx
            for idx, doc in enumerate(docs)
        }
        for i, fut in enumerate(as_completed(futures)):
            embeddings[futures[fut]] = fut.result()["embedding"]
            progress.progress((i + 1) / total)
    conn = connect_db()
    for embed, doc in zip(embeddings, docs):
        insert_document_chunk(
            conn,
            doc["content"],
            doc["metadata"],
            embed
        )
    conn.close()
    return raw_text

# ─── Main: Upload or Drag & Drop + Summarize ───────────────────────────────
st.markdown("#### Upload / Drag & Drop PDFs")
uploads = st.file_uploader(
    "Choose PDF(s)", type=["pdf"], accept_multiple_files=True
)
if uploads:
    for pdf in uploads:
        if pdf.name in st.session_state.processed_uploads:
            continue
        st.session_state.processed_uploads.add(pdf.name)
        path = os.path.join(PDF_DIR, pdf.name)
        with open(path, "wb") as f:
            f.write(pdf.read())
        with st.sidebar.spinner(f"Processing {pdf.name}…"):
            raw = process_pdf_in_parallel(path)
        st.sidebar.success(f"Indexed {pdf.name} ✅")
        summary = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"Please provide a concise summary (6–8 sentences) of:\n{raw[:4000]}"
            }]
        ).choices[0].message.content
        st.session_state.summaries[pdf.name] = summary
        st.sidebar.markdown("**📑 Summary:**")
        st.sidebar.write(summary)

# ─── Main: Chat Interface ─────────────────────────────────────────────────
# Render history for the selected session
for msg in st.session_state.chat_sessions[st.session_state.current_chat]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box for new question
user_q = st.chat_input("Ask a question about your PDFs…")
if user_q:
    # Append user message

    # 1) record it
        st.session_state.chat_sessions[st.session_state.current_chat].append({
           "role": "user", "content": user_q
        })
       
       # 2) show it immediately
        with st.chat_message("user"):
           st.markdown(user_q)
       
       # 3) now stream the assistant
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("🤖 Thinking…")
        try:
            response = send_pdf_answer(user_q)
            text = ""
            for c in response:
                text += c
                placeholder.markdown(text)
                time.sleep(0.01)
            # Append assistant reply
            st.session_state.chat_sessions[st.session_state.current_chat].append({
                "role": "assistant", "content": text
            })
        
        except Exception as e:
            placeholder.markdown(f"⚠️ Error: {e}")
