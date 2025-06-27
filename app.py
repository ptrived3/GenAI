# app.py
import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

ROLE_PROMPTS = {
    "math": "You are a math assistant...",
    "cs": "You are a CS tutor...",
    "career": "You are a career coach..."
}

st.title("🧠 Multi-Role Chatbot")

role = st.selectbox("Choose a role:", list(ROLE_PROMPTS.keys()))
user_input = st.text_input("Enter your message:")
send_btn = st.button("Send")

if send_btn and user_input:
    system_prompt = ROLE_PROMPTS[role]
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
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
        reply = response.json()["choices"][0]["message"]["content"]
        st.markdown(f"**🤖 Assistant:** {reply}")
    else:
        st.error("Something went wrong.")
