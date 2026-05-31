from __future__ import annotations

import json
from collections import Counter
from typing import Any, Optional

from redis import Redis

from app.core.models import ContextDoc, HotpotSample, SupportingFact
from app.core.processing import searchable_text, tokenize_text


class HotpotRepository:
    def __init__(self, redis_client: Redis, namespace: str = "hotpot") -> None:
        self.redis = redis_client
        self.namespace = namespace

    @classmethod
    def from_url(cls, redis_url: str, namespace: str = "hotpot") -> "HotpotRepository":
        return cls(Redis.from_url(redis_url, decode_responses=True), namespace=namespace)

    def _sample_key(self, sample_id: str) -> str:
        return f"{self.namespace}:sample:{sample_id}"

    def _index_key(self, kind: str, value: str) -> str:
        return f"{self.namespace}:index:{kind}:{value}"

    def _all_key(self) -> str:
        return f"{self.namespace}:index:all"

    def _serialize_sample(self, sample: HotpotSample) -> dict[str, str]:
        return {
            "id": sample.id,
            "subset": sample.subset,
            "split": sample.split,
            "question": sample.question,
            "answer": sample.answer,
            "type": sample.type,
            "level": sample.level,
            "context_docs_json": json.dumps([doc.__dict__ for doc in sample.context_docs], ensure_ascii=False),
            "supporting_facts_json": json.dumps(
                [fact.__dict__ for fact in sample.supporting_facts], ensure_ascii=False
            ),
        }

    def _deserialize_sample(self, mapping: dict[str, Any]) -> HotpotSample:
        context_docs = [ContextDoc(**item) for item in json.loads(mapping.get("context_docs_json", "[]"))]
        supporting_facts = [
            SupportingFact(**item) for item in json.loads(mapping.get("supporting_facts_json", "[]"))
        ]
        return HotpotSample(
            id=mapping["id"],
            subset=mapping.get("subset", ""),
            split=mapping.get("split", ""),
            question=mapping.get("question", ""),
            answer=mapping.get("answer", ""),
            type=mapping.get("type", ""),
            level=mapping.get("level", ""),
            context_docs=context_docs,
            supporting_facts=supporting_facts,
        )

    def ping(self) -> bool:
        return bool(self.redis.ping())

    def store_sample(self, sample: HotpotSample) -> None:
        pipe = self.redis.pipeline()
        self._queue_store_sample(pipe, sample)
        pipe.execute()

    def store_samples(self, samples: list[HotpotSample]) -> int:
        pipe = self.redis.pipeline()
        count = 0
        for sample in samples:
            self._queue_store_sample(pipe, sample)
            count += 1
        if count:
            pipe.execute()
        return count

    def _queue_store_sample(self, pipe, sample: HotpotSample) -> None:
        sample_key = self._sample_key(sample.id)
        pipe.hset(sample_key, mapping=self._serialize_sample(sample))
        pipe.sadd(self._all_key(), sample.id)
        pipe.sadd(self._index_key("split", sample.split), sample.id)
        pipe.sadd(self._index_key("type", sample.type), sample.id)
        pipe.sadd(self._index_key("level", sample.level), sample.id)

        for token in set(tokenize_text(searchable_text(sample))):
            pipe.sadd(self._index_key("token", token), sample.id)

    def get_sample(self, sample_id: str) -> Optional[HotpotSample]:
        mapping = self.redis.hgetall(self._sample_key(sample_id))
        if not mapping:
            return None
        return self._deserialize_sample(mapping)

    def list_sample_ids(self, limit: int = 20) -> list[str]:
        ids = sorted(self.redis.smembers(self._all_key()))
        return ids[:limit]

    def get_samples(self, sample_ids: list[str]) -> list[HotpotSample]:
        samples = []
        for sample_id in sample_ids:
            sample = self.get_sample(sample_id)
            if sample is not None:
                samples.append(sample)
        return samples

    def _filter_candidates(
        self,
        candidate_ids: set[str],
        *,
        split: str | None,
        question_type: str | None,
        level: str | None,
    ) -> set[str]:
        filtered = set(candidate_ids)
        if split:
            filtered &= set(self.redis.smembers(self._index_key("split", split)))
        if question_type:
            filtered &= set(self.redis.smembers(self._index_key("type", question_type)))
        if level:
            filtered &= set(self.redis.smembers(self._index_key("level", level)))
        return filtered

    def search_samples(
        self,
        query: str,
        *,
        split: Optional[str] = None,
        question_type: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        tokens = tokenize_text(query)
        score_counter: Counter[str] = Counter()

        if tokens:
            candidate_ids: set[str] = set()
            for token in tokens:
                token_ids = set(self.redis.smembers(self._index_key("token", token)))
                candidate_ids |= token_ids
                score_counter.update(token_ids)
        else:
            candidate_ids = set(self.redis.smembers(self._all_key()))

        candidate_ids = self._filter_candidates(
            candidate_ids, split=split, question_type=question_type, level=level
        )

        results = []
        for sample_id in candidate_ids:
            sample = self.get_sample(sample_id)
            if sample is None:
                continue
            score = float(score_counter.get(sample_id, 0))
            if not tokens:
                score = 1.0
            score += len(sample.supporting_facts) * 0.1 + len(sample.context_docs) * 0.05
            results.append(
                {
                    "id": sample.id,
                    "question": sample.question,
                    "answer": sample.answer,
                    "type": sample.type,
                    "level": sample.level,
                    "score": round(score, 2),
                }
            )

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:limit]

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_samples": self.redis.scard(self._all_key()),
            "by_split": self._count_index_values("split"),
            "by_type": self._count_index_values("type"),
            "by_level": self._count_index_values("level"),
        }

    def _count_index_values(self, kind: str) -> dict[str, int]:
        values = {}
        pattern = self._index_key(kind, "*")
        for key in self.redis.scan_iter(match=pattern):
            value = key.rsplit(":", 1)[-1]
            values[value] = self.redis.scard(key)
        return dict(sorted(values.items()))
