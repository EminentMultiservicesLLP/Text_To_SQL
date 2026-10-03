from retriever import retrieve_sql
from sql_generator import generate_sql
from vector_store import store
from validator import validate
from sql_executor import run

while True:

    q = input("\nYou: ")

    sql, emb = retrieve_sql(q)

    if not sql:
        print("LLM generating SQL...")
        sql = generate_sql(q)
        store(q, sql, emb)

    sql = validate(sql)

    print("\nSQL →", sql)

    result = run(sql)

    print("\nResult →", result)