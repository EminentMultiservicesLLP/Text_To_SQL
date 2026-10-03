"""
Vector Store
------------
Two-tier semantic cache using ChromaDB (embedded, no separate server).

Tier 1 — Full cache  (similarity >= FULL_CACHE_THRESHOLD, default 0.98):
  Identical or near-identical question. Re-execute cached SQL and return
  the cached answer text. Zero LLM calls.

Tier 2 — SQL cache   (similarity >= SIMILARITY_THRESHOLD, default 0.92):
  Similar but not identical question. Reuse the cached SQL (skip SQL-gen LLM)
  but re-execute against live data and re-format the fresh result.

Below threshold: full pipeline — both LLM calls, result stored afterwards.
"""
import uuid
import logging
import json
from dataclasses import dataclass
from typing import Literal
import chromadb
from chromadb.config import Settings
from config.settings import CHROMA_PATH, SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)

# Full-cache threshold: question is essentially identical → skip everything
FULL_CACHE_THRESHOLD = 0.98

_client = chromadb.PersistentClient(
    path=CHROMA_PATH,
    settings=Settings(anonymized_telemetry=False),
)
_collection = _client.get_or_create_collection(
    name="sql_cache_v2",
    metadata={"hnsw:space": "cosine"},
)


@dataclass
class CacheResult:
    tier: Literal["full", "sql", "miss"]
    sql: str | None = None
    answer: str | None = None
    chart: object = None   # ChartConfig | None — avoid circular import
    similarity: float = 0.0


def store(question: str, sql: str, answer: str, embedding: list[float], chart=None) -> None:
    """Persist a question → SQL + answer + chart config with its embedding."""
    chart_json = ""
    if chart is not None:
        try:
            import dataclasses
            chart_json = json.dumps(dataclasses.asdict(chart))
        except Exception:
            pass
    _collection.add(
        ids=[str(uuid.uuid4())],
        documents=[question],
        embeddings=[embedding],
        metadatas=[{"sql": sql, "answer": answer, "chart": chart_json}],
    )
    logger.debug("Cached Q→SQL+answer for: %.60s", question)


def find_similar(embedding: list[float]) -> CacheResult:
    """
    Search the cache and return a CacheResult indicating which tier was hit.
    """
    if _collection.count() == 0:
        return CacheResult(tier="miss")

    results = _collection.query(
        query_embeddings=[embedding],
        n_results=1,
        include=["metadatas", "distances", "documents"],
    )

    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    if not distances:
        return CacheResult(tier="miss")

    similarity = 1.0 - distances[0]
    meta = metadatas[0]
    matched_q = documents[0]

    if similarity >= FULL_CACHE_THRESHOLD:
        logger.info("FULL cache hit (%.3f) — matched: %.60s", similarity, matched_q)
        chart = _deserialize_chart(meta.get("chart", ""))
        return CacheResult(tier="full", sql=meta["sql"], answer=meta["answer"], chart=chart, similarity=similarity)

    if similarity >= SIMILARITY_THRESHOLD:
        logger.info("SQL cache hit (%.3f) — matched: %.60s", similarity, matched_q)
        return CacheResult(tier="sql", sql=meta["sql"], similarity=similarity)

    logger.info("Cache miss (%.3f)", similarity)
    return CacheResult(tier="miss", similarity=similarity)


def _deserialize_chart(chart_json: str):
    """Restore a ChartConfig from its JSON representation."""
    if not chart_json:
        return None
    try:
        from core.chart_advisor import ChartConfig
        data = json.loads(chart_json)
        return ChartConfig(**data)
    except Exception:
        return None
