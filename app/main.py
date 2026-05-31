from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError

from app.core.clustering import cluster_records
from app.core.graph import build_reasoning_graph
from app.services.repository import HotpotRepository

DEFAULT_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def create_app(repository=None) -> FastAPI:
    app = FastAPI(title="HotpotQA Redis Dashboard API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.repository = repository or HotpotRepository.from_url(DEFAULT_REDIS_URL)

    def get_repository() -> HotpotRepository:
        return app.state.repository

    @app.get("/api/health")
    def health(repository: HotpotRepository = Depends(get_repository)):
        try:
            redis_ok = repository.ping() if hasattr(repository, "ping") else True
        except RedisError as exc:
            raise HTTPException(status_code=503, detail=f"Redis unavailable: {exc}") from exc
        return {"status": "ok", "redis": redis_ok}

    @app.get("/api/search")
    def search(
        q: str = Query(default=""),
        split: Optional[str] = None,
        question_type: Optional[str] = Query(default=None, alias="type"),
        level: Optional[str] = None,
        limit: int = Query(default=10, ge=1, le=100),
        repository: HotpotRepository = Depends(get_repository),
    ):
        try:
            results = repository.search_samples(
                q,
                split=split,
                question_type=question_type,
                level=level,
                limit=limit,
            )
        except RedisError as exc:
            raise HTTPException(status_code=503, detail=f"Search failed: {exc}") from exc
        return {"query": q, "count": len(results), "results": results}

    @app.get("/api/sample/{sample_id}")
    def sample(sample_id: str, repository: HotpotRepository = Depends(get_repository)):
        try:
            record = repository.get_sample(sample_id)
        except RedisError as exc:
            raise HTTPException(status_code=503, detail=f"Sample lookup failed: {exc}") from exc
        if record is None:
            raise HTTPException(status_code=404, detail="Sample not found")
        return record.to_dict()

    @app.get("/api/path/{sample_id}")
    def path(sample_id: str, repository: HotpotRepository = Depends(get_repository)):
        try:
            record = repository.get_sample(sample_id)
        except RedisError as exc:
            raise HTTPException(status_code=503, detail=f"Path lookup failed: {exc}") from exc
        if record is None:
            raise HTTPException(status_code=404, detail="Sample not found")
        return build_reasoning_graph(record)

    @app.get("/api/cluster")
    def cluster(
        q: str = Query(default=""),
        split: Optional[str] = None,
        question_type: Optional[str] = Query(default=None, alias="type"),
        level: Optional[str] = None,
        limit: int = Query(default=25, ge=1, le=100),
        repository: HotpotRepository = Depends(get_repository),
    ):
        try:
            search_results = repository.search_samples(
                q,
                split=split,
                question_type=question_type,
                level=level,
                limit=limit,
            )
            samples = [repository.get_sample(item["id"]) for item in search_results]
        except RedisError as exc:
            raise HTTPException(status_code=503, detail=f"Cluster build failed: {exc}") from exc

        valid_samples = [sample for sample in samples if sample is not None]
        clusters = cluster_records(valid_samples)
        return {"query": q, "count": len(clusters), "clusters": clusters}

    @app.get("/api/stats")
    def stats(repository: HotpotRepository = Depends(get_repository)):
        try:
            return repository.get_stats()
        except RedisError as exc:
            raise HTTPException(status_code=503, detail=f"Stats failed: {exc}") from exc

    return app


app = create_app()
