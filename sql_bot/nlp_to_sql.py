# sql_bot/nlp_to_sql.py

import os
from dotenv import load_dotenv
from sqlalchemy import inspect
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .database import engine
from .prompt_templates import SQL_PROMPT

load_dotenv()

# LangChain OpenAI chat model
llm = ChatOpenAI(
    model="gpt-4o",            # pick your OpenAI model
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Compose: prompt -> model -> string
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful, friendly assistant that outputs ONLY a valid SQL query."),
        ("user", SQL_PROMPT),
    ]
)
chain = prompt | llm | StrOutputParser()

def generate_sql(question: str) -> str:
    """
    Introspect the DB schema, feed it to the LangChain pipeline,
    and return a single SQL query string.
    """
    # Reflect schema
    inspector = inspect(engine)
    table_info_lines = []
    for table_name in inspector.get_table_names():
        cols = inspector.get_columns(table_name)
        col_defs = ", ".join(f"{c['name']} {c['type']}" for c in cols)
        table_info_lines.append(f"{table_name}({col_defs})")
    table_info = "\n".join(table_info_lines)

    # Invoke the chain
    sql = chain.invoke({"table_info": table_info, "question": question}).strip()
    return sql


# import os
# from dotenv import load_dotenv
# from openai import OpenAI
# from sqlalchemy import inspect
# from .database import engine
# from .prompt_templates import SQL_PROMPT

# # Load env vars
# load_dotenv()

# # Initialize OpenAI client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def generate_sql(question: str) -> str:
#     """
#     Introspect the DB schema, build a prompt, and ask OpenAI for a single SQL query.
#     """
#     # 1️⃣ Reflect your tables & columns
#     inspector = inspect(engine)
#     table_info_lines = []
#     for table_name in inspector.get_table_names():
#         cols = inspector.get_columns(table_name)
#         col_defs = ", ".join(f"{c['name']} {c['type']}" for c in cols)
#         table_info_lines.append(f"{table_name}({col_defs})")
#     table_info = "\n".join(table_info_lines)

#     # 2️⃣ Build the prompt
#     prompt = SQL_PROMPT.format(
#         table_info=table_info,
#         question=question
#     )

#     # 3️⃣ Ask OpenAI for SQL
#     resp = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": "You are a helpful, friendly assistant that outputs ONLY a valid SQL query."},
#             {"role": "user",   "content": prompt}
#         ]
#     )

#     # 4️⃣ Return the generated SQL
#     sql = resp.choices[0].message.content.strip()
#     return sql
