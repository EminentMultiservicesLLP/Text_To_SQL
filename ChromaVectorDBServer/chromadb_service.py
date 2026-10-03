import chromadb
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Persistent DB folder
client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory="chroma_storage",
        anonymized_telemetry=False
    )
)

collection = client.get_or_create_collection(name="sql_memory")


# ---------- REQUEST MODELS ----------

class AddRequest(BaseModel):
    id: str
    text: str
    embedding: list


class SearchRequest(BaseModel):
    embedding: list
    k: int = 3


# ---------- API ----------

@app.post("/add")
def add_vector(req: AddRequest):
    collection.add(
        ids=[req.id],
        documents=[req.text],
        embeddings=[req.embedding]
    )
    client.persist()
    return {"status": "stored"}


@app.post("/search")
def search_vector(req: SearchRequest):
    result = collection.query(
        query_embeddings=[req.embedding],
        n_results=req.k
    )

    return result