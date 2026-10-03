"""
HTTP API used by the Blazor app. Run on the same server, bound to 127.0.0.1:
    python -m uvicorn datachat.api:create_app --factory --host 127.0.0.1 --port 8765
"""
import logging
import secrets
import threading
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from datachat.config import load_settings
from datachat.report import build_report, report_markdown
from datachat.service import ChatRequest, ChatResponse, ChatService, FeedbackRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


class TermDecision(BaseModel):
    term: str
    target: str
    approve: bool
    decided_by: str


def create_app(service: ChatService | None = None) -> FastAPI:
    svc = service or ChatService(load_settings())
    api_key = svc.settings.api_key

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        threading.Thread(target=svc.warm_up, daemon=True).start()
        yield

    app = FastAPI(title="DataChat engine", version="0.1.0", lifespan=lifespan)

    def require_key(x_api_key: str | None = Header(default=None)):
        if api_key and not (x_api_key and secrets.compare_digest(x_api_key, api_key)):
            raise HTTPException(status_code=401, detail="Invalid API key")

    def client_or_404(client_id: str):
        if client_id not in svc.runtimes:
            raise HTTPException(status_code=404, detail=f"Unknown client '{client_id}'")

    @app.get("/health")
    def health():
        return {"status": "ok", "clients": sorted(svc.runtimes), "llm_enabled": svc.planner is not None}

    @app.post("/v1/chat", response_model=ChatResponse, dependencies=[Depends(require_key)])
    def chat(req: ChatRequest):
        return svc.chat(req)

    @app.post("/v1/feedback", dependencies=[Depends(require_key)])
    def feedback(req: FeedbackRequest):
        svc.feedback(req)
        return {"ok": True}

    @app.get("/v1/clients/{client_id}", dependencies=[Depends(require_key)])
    def client_info(client_id: str):
        client_or_404(client_id)
        return svc.client_info(client_id)

    # ── admin: review what users taught the engine ─────────────────────────
    @app.get("/v1/admin/{client_id}/terms", dependencies=[Depends(require_key)])
    def terms(client_id: str):
        client_or_404(client_id)
        return {"suggested": svc.store.suggestions(client_id), "decided": svc.store.client_terms(client_id)}

    @app.post("/v1/admin/{client_id}/terms", dependencies=[Depends(require_key)])
    def decide(client_id: str, d: TermDecision):
        client_or_404(client_id)
        svc.store.decide(client_id, d.term, d.target, d.approve, d.decided_by)
        return {"ok": True}

    @app.get("/v1/admin/{client_id}/failed", dependencies=[Depends(require_key)])
    def failed(client_id: str, limit: int = 100):
        client_or_404(client_id)
        return svc.store.failed_questions(client_id, limit)

    @app.get("/v1/admin/{client_id}/report", dependencies=[Depends(require_key)])
    def report(client_id: str, days: int = 7, format: str = "json"):
        client_or_404(client_id)
        r = build_report(svc.store, client_id, max(1, min(days, 365)))
        return PlainTextResponse(report_markdown(r), media_type="text/markdown") if format == "md" else r

    @app.post("/v1/admin/reload", dependencies=[Depends(require_key)])
    def reload():
        svc.reload()
        counts = {c: svc.refresh_values(c) for c in svc.runtimes}
        return {"ok": True, "values_loaded": counts}

    return app
