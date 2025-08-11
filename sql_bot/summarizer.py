# sql_bot/summarizer.py

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .prompt_templates import SUMMARY_PROMPT

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY"),
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "You are a helpful, friendly assistant. Provide a concise, polite summary of the SQL results "
         "and highlight any insights (e.g., comparisons to averages)."),
        ("user", SUMMARY_PROMPT),
    ]
)
chain = prompt | llm | StrOutputParser()

def summarize(question: str, results: list[dict]) -> str:
    return chain.invoke({"question": question, "results": results}).strip()
