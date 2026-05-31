from __future__ import annotations

from collections import Counter

from app.core.models import HotpotSample
from app.core.processing import tokenize_text


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def cluster_records(
    records: list[HotpotSample], *, similarity_threshold: float = 0.35, max_keywords: int = 3
) -> list[dict]:
    clusters: list[dict] = []

    for record in records:
        token_set = set(tokenize_text(record.question))
        target_cluster = None

        for cluster in clusters:
            similarity = _jaccard_similarity(token_set, cluster["token_union"])
            if similarity >= similarity_threshold:
                target_cluster = cluster
                break

        if target_cluster is None:
            target_cluster = {
                "records": [],
                "token_union": set(),
                "token_counter": Counter(),
            }
            clusters.append(target_cluster)

        target_cluster["records"].append(record)
        target_cluster["token_union"].update(token_set)
        target_cluster["token_counter"].update(token_set)

    response = []
    for cluster in clusters:
        keywords = [token for token, _ in cluster["token_counter"].most_common(max_keywords)]
        response.append(
            {
                "label": " / ".join(keywords) if keywords else "misc",
                "size": len(cluster["records"]),
                "keywords": keywords,
                "sample_ids": [record.id for record in cluster["records"]],
            }
        )

    return sorted(response, key=lambda item: item["size"], reverse=True)
