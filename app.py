import streamlit as st
from genAI import send_pdf_answer
import time

st.set_page_config(page_title="PDF Chatbot", layout="centered")
st.title("PDF Chatbot")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ✅ 1. Display past messages (only previous ones)
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ✅ 2. Input and real-time response
user_input = st.chat_input("Ask a question about your PDFs...")



if user_input:
    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # Stream assistant response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("🤖 Thinking...")

        try:
            full_response = send_pdf_answer(user_input)
            streamed_text = ""

            for chunk in full_response:
                streamed_text += chunk
                response_placeholder.markdown(streamed_text)
                time.sleep(0.015)

            # ✅ Now save to history after rendering
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

        except Exception as e:
            response_placeholder.markdown(f"⚠️ Error: {e}")
