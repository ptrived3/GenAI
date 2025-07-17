# openai.py
import os
from queryChunks import get_top_k_chunks
from openai import OpenAI
from dotenv import load_dotenv

# Load OpenAI API key from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

You may only use the following content retrieved from PDFs to answer the user’s question. Do not guess or use outside knowledge.
If the answer is not found in the content below, respond:
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
    results = get_top_k_chunks(query, k=3)

    # Optional: debug print similarity scores
    for r in results:
        print(f"Score: {r[2]:.3f} | Preview: {r[0][:80]!r}")

    # Apply similarity filter
    relevant = [(r[0], r[1]) for r in results if r[2] < SIMILARITY_THRESHOLD]

    if not relevant:
        return "I'm sorry, but I couldn't find anything in the documents related to that question. I'd love to help you answer questions related to the solar system though!"

    system_prompt = build_context_prompt(relevant, query)
    return ask_openai(system_prompt, query)