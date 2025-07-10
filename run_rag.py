import os
import ollama  # or use openai if you'd rather go cloud
from queryChunks import get_top_k_chunks


def build_context_prompt(chunks, query):
    context = "\n\n".join([chunk[0] for chunk in chunks])  # chunk[0] = content
    return f"""You are a helpful assistant. Use the following PDF content to answer the user's question.

Context:
{context}

Question: {query}

Answer:"""


def ask_ollama(prompt, model="llama3"):  # or mistral/phi3 etc.
    response = ollama.chat(model=model, messages=[
        {"role": "user", "content": prompt}
    ])
    return response['message']['content'].strip()


if __name__ == "__main__":
    query = input("Ask your question: ")

    chunks = get_top_k_chunks(query)
    prompt = build_context_prompt(chunks, query)
    answer = ask_ollama(prompt)  # or swap in ask_openai()

    print("\n🤖 Answer:")
    print(answer)
