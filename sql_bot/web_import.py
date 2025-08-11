# sql_bot/web_import.py

import os
import pandas as pd
from serpapi import GoogleSearch
from .database import engine

def fetch_table(query: str) -> pd.DataFrame:
    """
    Use SerpAPI’s GoogleSearch client to scrape the first HTML table for the given query.
    """
    params = {
        "engine":  "google",
        "q":       query,
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }
    client = GoogleSearch(params)
    results = client.get_dict().get("organic_results", [])

    for r in results:
        url = r.get("link")
        try:
            tables = pd.read_html(url)
            if tables:
                return tables[0]
        except Exception:
            continue

    raise RuntimeError(f"No HTML table found for query {query!r}")

def load_df_to_sql(df: pd.DataFrame, table_name: str):
    """
    Write the DataFrame into Postgres under the given table name.
    """
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
