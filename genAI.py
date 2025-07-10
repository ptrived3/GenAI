# OpenAI.py
import os
import requests
from dotenv import load_dotenv
from generate_embeddings import get_embeddings_from_folder, find_relevant_chunks

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# Load all PDFs once at startup
FOLDER_PATH = "pdfs"
embedded_documents, model = get_embeddings_from_folder(FOLDER_PATH)

# ✨ Adaptive prompt retained
system_prompt = """
You are a helpful, thoughtful assistant capable of adapting to both the user’s needs and their tone.

Roles:
- If the user asks a math question, respond like a math tutor.
- If the user is asking for coding help, explain like a CS tutor.
- If the user starts talking about career paths or jobs, give professional career advice.

Tone Mirroring:
- Match the user's communication style. If they joke, feel free to joke back (while staying helpful and accurate).
- If they are formal, be formal. If they’re casual, respond casually.
- If unsure about the tone, default to polite and conversational.

Only use the following PDF content to answer the user's question.
If the answer cannot be found in the documents, politely say so.

Examples:
- User: "Yo bot, what’s 2+2 lmao?"
  Assistant: "Haha classic — it's 4, of course 😄"
- User: "Greetings. Could you assist me in understanding recursion?"
  Assistant: "Of course. Recursion is a process where a function calls itself..."
"""

def send_pdf_answer(query):
    relevant_chunks = find_relevant_chunks(query, embedded_documents, model)
    context = "\n\n".join([chunk["content"] for chunk in relevant_chunks])

    messages = [
        {"role": "system", "content": system_prompt + "\n\n" + context},
        {"role": "user", "content": query}
    ]

    json_data = {
        "model": "gpt-4o-mini",
        "messages": messages
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=json_data
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"OpenAI API Error {response.status_code}: {response.text}")


# # OpenAI.py
# import os
# import requests
# from dotenv import load_dotenv
# # from generate_embeddings import find_relevant_chunks
# from generate_embeddings import get_embeddings_from_folder


# load_dotenv()
# API_KEY = os.getenv("OPENAI_API_KEY")

# headers = {
#     "Authorization": f"Bearer {API_KEY}",
#     "Content-Type": "application/json",
# }

# # Prompt: Role + Tone Adaptive Assistant
# system_prompt = """
# You are a helpful, thoughtful assistant capable of adapting to both the user’s needs and their tone.

# Roles:
# - If the user asks a math question, respond like a math tutor.
# - If the user is asking for coding help, explain like a CS tutor.
# - If the user starts talking about career paths or jobs, give professional career advice.

# Tone Mirroring:
# - Match the user's communication style. If they joke, feel free to joke back (while staying helpful and accurate).
# - If they are formal, be formal. If they’re casual, respond casually.
# - If unsure about the tone, default to polite and conversational.

# General Guidelines:
# - Adapt your style depending on the topic — scientific, educational, technical, or practical.
# - Ask clarifying questions if needed.

# Examples:
# - User: "Yo bot, what’s 2+2 lmao?"
#   Assistant: "Haha classic — it's 4, of course 😄"
# - User: "Greetings. Could you assist me in understanding recursion?"
#   Assistant: "Of course. Recursion is a process where a function calls itself..."
# """

# # Initialize a new chat session
# def initialize_chat():
#     return [{"role": "system", "content": system_prompt}]

# # Send message to assistant and get response
# def send_message_to_assistant(messages, user_input):
#     messages.append({"role": "user", "content": user_input})

#     json_data = {
#         "model": "gpt-4o-mini",
#         "messages": messages
#     }

#     response = requests.post(
#         "https://api.openai.com/v1/chat/completions",
#         headers=headers,
#         json=json_data
#     )

#     if response.status_code == 200:
#         assistant_reply = response.json()["choices"][0]["message"]["content"]
#         messages.append({"role": "assistant", "content": assistant_reply})
#         return assistant_reply
#     else:
#         raise Exception(f"OpenAI API Error {response.status_code}: {response.text}")


# def send_pdf_answer(query, embedded_documents, model):
#     relevant_chunks = find_relevant_chunks(query, embedded_documents, model)

#     context = "\n\n".join([chunk["content"] for chunk in relevant_chunks])
#     messages = [
#         {
#             "role": "system",
#             "content": "You are a helpful assistant. Only use the following PDF content to answer:\n\n" + context
#         },
#         {
#             "role": "user",
#             "content": query
#         }
#     ]

#     json_data = {
#         "model": "gpt-4o-mini",
#         "messages": messages
#     }

#     response = requests.post(
#         "https://api.openai.com/v1/chat/completions",
#         headers=headers,
#         json=json_data
#     )

#     if response.status_code == 200:
#         return response.json()["choices"][0]["message"]["content"]
#     else:
#         raise Exception(f"OpenAI API Error {response.status_code}: {response.text}")
