# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv()

# API_KEY = os.getenv("OPENAI_API_KEY")

# headers = {
#     "Authorization": f"Bearer {API_KEY}",
#     "Content-Type": "application/json",
# }

# MATH_SYSTEM_PROMPT_BASE = """You are a highly specialized and STRICTLY MATHEMATICAL assistant.

# Your ABSOLUTE SOLE PURPOSE is to answer questions that are purely and explicitly related to mathematics. This includes arithmetic, algebra, geometry, calculus, statistics, mathematical logic, and other quantifiable or abstract mathematical concepts.

# You MUST follow these strict rules:

# 0. IF the user prompt does not contain a question, just introduce yourself and explain your purpose.
# 1. IF the user prompt contains a clear math question (such as "What is 2 + 2?", "Solve for x in x + 3 = 5", "What is the derivative of x^2?"), you MUST answer it in three sections:
#     - Question: Restate the question for clarity.
#     - Answer: Provide the direct answer.
#     - Explanation: Show step-by-step reasoning.
# 2. IF the user prompt is not a math question, you MUST refuse to answer using one of these polite responses:
#     - "I specialize solely in mathematical questions. Please ask me a math-related question."
#     - "My function is strictly limited to mathematics. I'm unable to assist with that inquiry."
#     - "That question falls outside my mathematical domain. I can only provide mathematical assistance."

# You must strictly adhere to this mathematical-only limitation.
# """

# json_data = {
#     "model": "gpt-4o-mini",
#     # "model": "gpt-4o",
#     "messages": [
#         {"role": "system", "content": MATH_SYSTEM_PROMPT_BASE},
#         {"role": "user", "content": "If all bloops are razzies, and all razzies are lazzies, are all bloops lazzies?"}
#     ]
# }

# response = requests.post(
#     "https://api.openai.com/v1/chat/completions",
#     headers=headers,
#     json=json_data,
# )

# print(response.status_code)
# print(response.json()["choices"][0]["message"]["content"])



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

# Timestamped chatlog filename
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
chatlog_filename = f"chatlog_{timestamp}.txt"

MATH_SYSTEM_PROMPT_BASE = """You are a highly specialized and STRICTLY MATHEMATICAL assistant.

Your ABSOLUTE SOLE PURPOSE is to answer questions that are purely and explicitly related to mathematics. This includes arithmetic, algebra, geometry, calculus, statistics, mathematical logic, and other quantifiable or abstract mathematical concepts.

You MUST follow these strict rules:

0. IF the user prompt does not contain a question, just introduce yourself and explain your purpose.
1. IF the user prompt contains a clear math question (such as "What is 2 + 2?", "Solve for x in x + 3 = 5", "What is the derivative of x^2?"), you MUST answer it in three sections:
    - Question: Restate the question for clarity.
    - Answer: Provide the direct answer.
    - Explanation: Show step-by-step reasoning.
2. IF the user prompt is not a math question, you MUST refuse to answer using one of these polite responses:
    - "I specialize solely in mathematical questions. Please ask me a math-related question."
    - "My function is strictly limited to mathematics. I'm unable to assist with that inquiry."
    - "That question falls outside my mathematical domain. I can only provide mathematical assistance."

You must strictly adhere to this mathematical-only limitation.
"""

# Initialize message history
messages = [{"role": "system", "content": MATH_SYSTEM_PROMPT_BASE}]

print(f"📐 Math Chatbot is ready! Type 'exit' to quit, 'clearlog' to reset the log.\nChat will be saved to {chatlog_filename}\n")

while True:
    user_input = input("👤 You: ").strip()

    # Exit condition
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break

    # Clear log mid-conversation
    if user_input.lower() == "clearlog":
        open(chatlog_filename, "w").close()
        print("🧹 Chatlog cleared!\n")
        continue

    messages.append({"role": "user", "content": user_input})

    json_data = {
        "model": "gpt-4o-mini",  # or "gpt-4o"
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

        # Live append to chatlog
        with open(chatlog_filename, "a") as f:
            f.write(f"User: {user_input}\n\n")
            f.write(f"Assistant: {reply}\n\n")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        break
