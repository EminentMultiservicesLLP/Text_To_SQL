import requests
import uuid

URL = "http://localhost:9000"


def store(text, embedding):
    requests.post(
        f"{URL}/add",
        json={
            "id": str(uuid.uuid4()),
            "text": text,
            "embedding": embedding
        }
    )


def search(embedding):
    r = requests.post(
        f"{URL}/search",
        json={"embedding": embedding, "k": 1}
    )

    data = r.json()

    if data["documents"][0]:
        return data["documents"][0][0]

    return None