"""HTTP routes for the demo: sign in as a role, ask, read the measured results, serve the UI."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Sequence
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles

from enterprise_rag.config import RagConfig
from enterprise_rag.llm import LLMError
from enterprise_rag.serving.limits import AnswerCache, RateLimiter
from enterprise_rag.serving.results import load_results
from enterprise_rag.serving.schemas import AskRequest, SessionRequest, ask_response
from enterprise_rag.serving.session import COOKIE, MAX_AGE_S, SessionSigner

log = logging.getLogger(__name__)
BUSY = "The answer service is busy or unavailable. Please try again in a minute."


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "?")


def create_app(pipeline, cfg: RagConfig, roles: Sequence[str], meta: dict, runs_dir: Path,
               static_dir: Path | None = None, secret: str | None = None) -> FastAPI:
    app = FastAPI(title="Enterprise RAG demo", docs_url="/api/docs", openapi_url="/api/openapi.json")
    signer = SessionSigner(roles, secret)
    limiter = RateLimiter(cfg.rate_per_minute, cfg.rate_per_day)
    cache = AnswerCache()
    lock = threading.Lock()  # one answer at a time: the Groq quota is the bottleneck anyway

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/meta")
    def get_meta() -> dict:
        return {**meta, "limits": {"max_question_chars": cfg.max_question_chars,
                                   "per_minute": cfg.rate_per_minute,
                                   "per_day": cfg.rate_per_day}}

    @app.post("/api/session")
    def start_session(body: SessionRequest, response: Response) -> dict:
        if body.role not in roles:
            raise HTTPException(422, f"Unknown role. Choose one of: {', '.join(roles)}.")
        response.set_cookie(COOKIE, signer.issue(body.role), max_age=MAX_AGE_S, httponly=True,
                            samesite="lax")
        return {"role": body.role}

    @app.post("/api/ask")
    def ask(body: AskRequest, request: Request) -> dict:
        role = signer.verify(request.cookies.get(COOKIE))
        if role is None:
            raise HTTPException(401, "Choose a role to sign in before asking.")
        question = body.question.strip()
        if not question or len(question) > cfg.max_question_chars:
            raise HTTPException(
                422, f"Ask a question between 1 and {cfg.max_question_chars} characters.")
        cached = cache.get(role, question)
        if cached is not None:
            return {**cached, "cached": True}
        wait = limiter.check(_client_key(request))
        if wait:
            raise HTTPException(429, f"Too many questions. Try again in {wait} seconds.",
                                headers={"Retry-After": str(wait)})
        start = time.perf_counter()
        try:
            with lock:
                resp = pipeline.answer(question, role)
        except LLMError as exc:
            log.warning("ask failed: %s", exc)
            raise HTTPException(503, BUSY) from exc
        result = {**ask_response(resp, role, question),
                  "latency_ms": round((time.perf_counter() - start) * 1000)}
        cache.put(role, question, result)
        return {**result, "cached": False}

    @app.get("/api/results")
    def results() -> dict:
        return load_results(runs_dir)

    if static_dir is not None and (static_dir / "index.html").exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")
    return app
