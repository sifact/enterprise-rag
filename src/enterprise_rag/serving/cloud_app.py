"""The deployed API: Qdrant Cloud search, Groq models, exported meta and results snapshots.

Imports stay light (no pandas, local models or DeepEval) so it fits a serverless function.
Configuration comes from environment variables set on the host, never from the repo.
"""

from __future__ import annotations

import json
import os
from dataclasses import replace

from fastapi import FastAPI
from qdrant_client import QdrantClient

from enterprise_rag.config import PROJECT_ROOT, load_eval_config, load_rag_config
from enterprise_rag.generation import Generator
from enterprise_rag.guardrails import InjectionGuard, groq_scorer
from enterprise_rag.llm import GroqClient
from enterprise_rag.pipeline.rag import RagPipeline
from enterprise_rag.retrieval.cloud import CloudRetriever
from enterprise_rag.serving.app import create_app

DEPLOY_DIR = PROJECT_ROOT / "deploy"
SAFETY_SUFFIX = "_safety"  # the demo searches the collection that includes the poisoned pages


def build_cloud_rag(client: QdrantClient, collection: str) -> RagPipeline:
    rag, ev = load_rag_config(), load_eval_config()
    retriever = CloudRetriever(client, collection, mode=rag.cloud_mode, fusion=rag.cloud_fusion,
                               dense_model=rag.cloud_dense_model,
                               sparse_model=rag.cloud_sparse_model,
                               prefetch_limit=rag.prefetch_limit, name="rag-cloud")
    generator = Generator(GroqClient(rag.generator_model, ev.tokens_per_minute,
                                     extra_body={"reasoning_format": "hidden"}))
    guard = InjectionGuard(groq_scorer(GroqClient(rag.guard_model, ev.tokens_per_minute)),
                           rag.guard_threshold)
    return RagPipeline(retriever, guard, generator,
                       replace(rag, evidence_threshold=rag.cloud_evidence_threshold),
                       name="rag-cloud",
                       evidence=lambda question, role, chunks: retriever.evidence(question, role))


def cloud_client() -> QdrantClient:
    return QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"],
                        cloud_inference=True, timeout=30)


def make_app() -> FastAPI:
    rag = load_rag_config()
    meta = json.loads((DEPLOY_DIR / "meta.json").read_text())
    results = json.loads((DEPLOY_DIR / "results.json").read_text())
    roles = [r["name"] for r in meta["roles"]]
    pipeline = build_cloud_rag(cloud_client(), rag.cloud_collection + SAFETY_SUFFIX)
    return create_app(pipeline, rag, roles, meta, runs_dir=None, results=results,
                      secret=os.environ["SESSION_SECRET"])
