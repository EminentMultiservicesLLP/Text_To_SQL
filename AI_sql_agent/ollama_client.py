import requests
from config import *

def get_embedding(text):
    r = requests.post(f"{OLLAMA_URL}/api/embeddings", json={
        "model": EMBED_MODEL,
        "prompt": text
    })
    return r.json()["embedding"]


def generate(prompt):
    r = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False
    })
    return r.json()["response"].strip()



