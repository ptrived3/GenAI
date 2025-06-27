# This code initializes a simple command-line chatbot that interacts with the OpenAI API to answer mathematical questions.
# It uses a strict mathematical prompt to ensure the assistant only responds to math-related queries.
# The conversation history is maintained to provide context for the assistant's responses.
# The user can exit the chat by typing 'exit' or 'quit'.
# The code handles errors gracefully and provides feedback to the user.


import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# ----------- MULTI-ROLE SETUP -----------

ROLE_PROMPTS = {
    "math": """You are a highly specialized and STRICTLY MATHEMATICAL assistant.
Your ABSOLUTE SOLE PURPOSE is to answer questions that are purely and explicitly related to mathematics...""",
    "cs": """You are a helpful assistant who explains computer science topics to a student. Use clear, beginner-friendly language with examples if possible.""",
    "career": """You are a professional career coach. You help users with resume tips, interview prep, and job search strategies."""
}

# Ask user which role to load
print("🤖 Choose a role: [math, cs, career]")
role = input("Enter role: ").strip().lower()

if role not in ROLE_PROMPTS:
    print("❌ Invalid role selected. Defaulting to 'math'.")
    role = "math"

system_prompt = ROLE_PROMPTS[role]

# ----------- SETUP LOGGING -----------

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
chatlog_filename = f"chatlog.txt"

messages = [{"role": "system", "content": system_prompt}]

print(f"\n🧠 Role selected: {role}")
print("💬 Type 'exit' to quit, 'clearlog' to reset log.\n")

while True:
    user_input = input("👤 You: ").strip()

    if user_input.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break

    if user_input.lower() == "clearlog":
        open(chatlog_filename, "w").close()
        print("🧹 Chatlog cleared!\n")
        continue

    messages.append({"role": "user", "content": user_input})

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
        reply = response.json()["choices"][0]["message"]["content"]
        print(f"\n🤖 Assistant: {reply}\n")
        messages.append({"role": "assistant", "content": reply})

        with open(chatlog_filename, "a") as f:
            f.write(f"User: {user_input}\n\n")
            f.write(f"Assistant: {reply}\n\n")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        break