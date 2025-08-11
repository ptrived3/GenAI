# quick_test.py
from sql_bot.main import handle_query

tests = [
    "List all products with price over 15 dollars, show name and price, cheapest first.",
    "Total revenue by product (price * quantity). Show product name and total revenue, top 5.",
    "Orders per month in 2024 with total quantity.",
    "Average order quantity per product, descending.",
]

for q in tests:
    out = handle_query(q)
    print("\nQ:", q)
    print("SQL:", out.get("sql"))
    if "error" in out:
        print("ERROR:", out["error"])
    else:
        print(out["table"])
        print("Summary:", out["summary"])
