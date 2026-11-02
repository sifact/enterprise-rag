"""Request bodies and the JSON shape of an answer, built from a pipeline response."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_rag.retrieval.types import PipelineResponse

SNIPPET_CHARS = 700


class SessionRequest(BaseModel):
    role: str


class AskRequest(BaseModel):
    # Unknown fields such as "role" are ignored: the role comes from the signed session.
    model_config = ConfigDict(extra="ignore")
    question: str


def ask_response(resp: PipelineResponse, role: str, question: str) -> dict:
    trace = resp.trace or {}
    used = trace.get("used") or [c.chunk_id for c in resp.retrieved]
    removed = {r["chunk_id"]: r["reason"] for r in trace.get("removed", [])}
    cleaned = {r["chunk_id"]: r["reason"] for r in trace.get("cleaned", [])}
    by_id = {c.chunk_id: c for c in resp.retrieved}

    def number(chunk_id: str, fallback: int) -> int:
        """The [n] the answer text uses: the passage's position among those given to the model."""
        return used.index(chunk_id) + 1 if chunk_id in used else fallback

    citations = []
    for i, cid in enumerate(resp.citations, start=1):
        c = by_id.get(cid)
        meta = c.meta if c else {}
        citations.append({"n": number(cid, i), "chunk_id": cid, "doc_id": c.doc_id if c else "",
                          "title": meta.get("title"), "section": meta.get("section"),
                          "page": meta.get("page"), "source_url": meta.get("source_url"),
                          "snippet": (c.text[:SNIPPET_CHARS] if c else "")})
    retrieved = [{"chunk_id": c.chunk_id, "doc_id": c.doc_id, "title": c.meta.get("title"),
                  "section": c.meta.get("section"), "page": c.meta.get("page"),
                  "allowed_roles": c.meta.get("allowed_roles") or [],
                  "score": round(c.score, 4),
                  "rerank_score": None if c.rerank_score is None else round(c.rerank_score, 3),
                  "cited": c.chunk_id in resp.citations, "used": c.chunk_id in used,
                  "removed_reason": removed.get(c.chunk_id),
                  "cleaned_reason": cleaned.get(c.chunk_id),
                  "snippet": c.text[:SNIPPET_CHARS]}
                 for c in resp.retrieved]
    usage = resp.usage
    return {
        "role": role, "question": question, "answer": resp.text, "refused": resp.refused,
        "refusal_reason": trace.get("refusal_reason"), "citations": citations,
        "retrieved": retrieved, "removed": trace.get("removed", []),
        "cleaned": trace.get("cleaned", []),
        "guard": trace.get("guard"), "timings": trace.get("stages", {}),
        "top_score": trace.get("top_score"), "model": trace.get("model"),
        "prompt_version": trace.get("prompt_version"),
        "usage": {"prompt_tokens": usage.prompt_tokens,
                  "completion_tokens": usage.completion_tokens} if usage else None,
    }
