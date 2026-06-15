from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

from app.core.clustering import cluster_records
from app.core.graph import build_reasoning_graph
from app.core.processing import normalize_hotpot_record


def main() -> None:
    limit = 50
    print(f"正在从 HuggingFace 加载 hotpotqa/hotpot_qa (distractor, validation)...")

    dataset = load_dataset("hotpotqa/hotpot_qa", "distractor", split="validation")
    samples = []
    for raw in dataset:
        samples.append(normalize_hotpot_record(raw, subset="distractor", split="validation"))
        if len(samples) >= limit:
            break

    print(f"已加载 {len(samples)} 条样本")

    by_type = {}
    by_level = {}
    by_split = {"validation": len(samples)}
    for s in samples:
        by_type[s.type] = by_type.get(s.type, 0) + 1
        by_level[s.level] = by_level.get(s.level, 0) + 1

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "total_samples": len(samples),
            "by_split": by_split,
            "by_type": by_type,
            "by_level": by_level,
        },
        "records": [s.to_dict() for s in samples],
        "paths": {s.id: build_reasoning_graph(s) for s in samples},
        "clusters": cluster_records(samples),
    }

    output_path = Path("docs/data/demo_samples.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已导出 {len(samples)} 条样本到 {output_path}")
    print(f"  bridge: {by_type.get('bridge', 0)}, comparison: {by_type.get('comparison', 0)}")
    print(f"  easy: {by_level.get('easy', 0)}, medium: {by_level.get('medium', 0)}, hard: {by_level.get('hard', 0)}")


if __name__ == "__main__":
    main()
