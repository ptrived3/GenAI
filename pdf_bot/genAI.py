# genAI.py
import os
import re
from pdf_bot.queryChunks import get_top_k_chunks
from openai import OpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
import psycopg2
import pandas as pd


# Load OpenAI API key from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def connect_db():
    """Used by tests (and can replace the inline connect in run_sql_query)."""
    return psycopg2.connect(
        dbname=os.getenv("LLM_SQL_DBNAME", "llm_sql_demo"),
        user=os.getenv("DB_USER",        "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST",        "localhost")
    )

# Adjust this threshold based on similarity scores you've tested
SIMILARITY_THRESHOLD = 20.0

# 🎯 System prompt — includes adaptive tone instructions
system_prompt_template = """
You are a helpful, thoughtful assistant capable of adapting to both the user’s needs and their tone.

Roles:
- If the user asks a math question, respond like a math tutor.
- If the user is asking for coding help, explain like a CS tutor.
- If the user starts talking about career paths or jobs, give professional career advice.

Tone Mirroring:
- Match the user's communication style. If they joke, joke back (while staying helpful and accurate).
- If they are formal, be formal. If they’re casual, respond casually.
- If unsure, default to polite and conversational.

You may only use the content below (from the PDFs) to answer.  
You may also **infer synonyms or antonyms** from that content—for example, if the text says “the Sun is dynamic,” then “static” means “not dynamic.”  
If the answer cannot be found or reasonably inferred from this content, respond:
"I'm sorry, but I couldn't find anything in the documents related to that question."

---

PDF Context:
{context}
---
"""

def build_context_prompt(chunks, query):
    formatted_chunks = []
    for chunk in chunks:
        content = chunk[0][:500]
        meta = chunk[1]  # metadata dict
        label = f"[{meta['source']} - chunk {meta['chunk_index']}]"
        formatted_chunks.append(f"{label}\n{content}")
    
    context_block = "\n\n".join(formatted_chunks)
    return system_prompt_template.format(context=context_block)

def ask_openai(system_prompt, user_query):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    )
    return response.choices[0].message.content.strip()

def send_pdf_answer(query):
    # 1) Semantic search
    results = get_top_k_chunks(query, k=3)

    # Debug: print scores
    for r in results:
        print(f"Score: {r[2]:.3f} | Preview: {r[0][:80]!r}")

    # 2) Similarity filter
    semantic_hits = [(r[0], r[1]) for r in results if r[2] < SIMILARITY_THRESHOLD]

    # 3) If no semantic match, decline
    if not semantic_hits:
        return "I'm sorry, but I couldn't find anything in the documents related to that question."

    # 4) Lexical overlap guard
    #   extract query words of length >3 (to skip 'the', 'is', etc.)
    query_terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 3]
    #   check if any term appears in any chunk
    has_overlap = any(
        any(term in chunk_text.lower() for term in query_terms)
        for chunk_text, _ in semantic_hits
    )
    if not has_overlap:
        return "I'm sorry, but I couldn't find anything in the documents related to that question."

    # 5) Build prompt & call OpenAI
    system_prompt = build_context_prompt(semantic_hits, query)
    return ask_openai(system_prompt, query)

# ─── NL→SQL Setup (LangChain PromptTemplate) ─────────────────────────────
# template_str = open("prompt_template.sql.j2").read()
HERE = os.path.dirname(__file__)
template_path = os.path.join(HERE, "prompt_template.sql.j2")
with open(template_path, "r") as f:
    template_str = f.read()
sql_prompt = PromptTemplate(
    input_variables=["schema_description", "user_question"],
    template=template_str
)

SCHEMA_DESCRIPTION = """
products(product_id serial, name text, price numeric)
orders(order_id serial, customer text, order_date date)
order_items(order_item_id serial, order_id int, product_id int, quantity int)
"""

def generate_sql(nl_question: str) -> str:
    prompt = sql_prompt.format(
        schema_description=SCHEMA_DESCRIPTION,
        user_question=nl_question
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()

def run_sql_query(sql: str):
    # ── CLEAN MARKDOWN FENCES ──
    lines = sql.splitlines()
    # drop any lines that start with ``` (```sql or ```)
    lines = [l for l in lines if not l.strip().startswith("```")]
    clean_sql = "\n".join(lines).strip()

    # ── EXECUTE AGAINST THE DB ──
    conn = connect_db()
    with conn.cursor() as cur:
        cur.execute(clean_sql)
        try:
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=cols)
        except psycopg2.ProgrammingError:
            df = pd.DataFrame()
    conn.commit()
    conn.close()
    return df



if __name__ == "__main__":
    # 1) Prompt yourself for a natural‐language question
    nlq = input("Ask your NL→SQL question: ")

    # 2) Generate the SQL
    sql = generate_sql(nlq)
    print("\n Generated SQL:\n", sql)

    # 3) Run it against Postgres
    results = run_sql_query(sql)
    print("\n Results:", results)
