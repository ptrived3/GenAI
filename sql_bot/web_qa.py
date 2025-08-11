# sql_bot/web_qa.py
import os, re, requests, bs4
from typing import Tuple, Optional
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

# Load API key from .env no matter where you're running from
load_dotenv(find_dotenv())

llm = ChatOpenAI(
    model="gpt-4o-mini",  # or gpt-4o if you want
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

PREFERRED = ("nasa.gov", "wikipedia.org", "britannica.com", "esa.int", "noirlab.edu")

def _first_good_url(query: str) -> Optional[str]:
    results = DuckDuckGoSearchAPIWrapper().results(query, max_results=8)
    def ok(u): return u and not u.lower().endswith((".pdf", ".ppt", ".doc", ".docx"))
    # 1) prefer allowlisted domains
    for r in results:
        url = r.get("link")
        if ok(url) and any(d in url for d in PREFERRED):
            return url
    # 2) otherwise first decent result
    for r in results:
        url = r.get("link")
        if ok(url):
            return url
    return None

def _fetch_text(url: str) -> str:
    html = requests.get(url, timeout=15).text
    soup = bs4.BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = " ".join(t.strip() for t in soup.get_text(" ").split())
    return text[:12000]

EXTRACT_PROMPT = """You are a precise extractor.
Question: {question}
Web page text (may be long and noisy):
---
{text}
---
Return ONLY the short factual answer as a few words or a number (no extra text).
If not answerable, return "UNKNOWN".
"""

_extract_chain = ChatPromptTemplate.from_template(EXTRACT_PROMPT) | llm | StrOutputParser()

def answer_from_web(question: str) -> Tuple[Optional[str], Optional[str]]:
    url = _first_good_url(question)
    if not url:
        return None, None
    text = _fetch_text(url)
    resp = _extract_chain.invoke({"question": question, "text": text}).strip()
    resp = re.sub(r'^\s*Answer:\s*', '', resp, flags=re.I)
    if not resp or resp.upper() == "UNKNOWN":
        return None, None
    return resp, url
