from ollama_client import get_embedding
from vector_store import search_similar

def retrieve_sql(question):
    emb = get_embedding(question)
    sql = search_similar(emb)
    return sql, emb