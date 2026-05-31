from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.clustering import cluster_records
from app.core.graph import build_reasoning_graph
from app.services.repository import HotpotRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export demo JSON for GitHub Pages")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", default="docs/data/demo_samples.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository = HotpotRepository.from_url(args.redis_url)
    sample_ids = repository.list_sample_ids(limit=args.limit)
    samples = repository.get_samples(sample_ids)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": repository.get_stats(),
        "records": [sample.to_dict() for sample in samples],
        "paths": {sample.id: build_reasoning_graph(sample) for sample in samples},
        "clusters": cluster_records(samples),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(samples)} samples to {output_path}")


if __name__ == "__main__":
    main()
