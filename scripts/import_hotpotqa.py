from __future__ import annotations

import argparse

from datasets import load_dataset

from app.core.processing import normalize_hotpot_record
from app.services.repository import HotpotRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import HotpotQA records into Redis")
    parser.add_argument("--subset", default="distractor", choices=["distractor", "fullwiki"])
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--redis-url", default="redis://localhost:6379/0")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = load_dataset("hotpotqa/hotpot_qa", args.subset, split=args.split)
    repository = HotpotRepository.from_url(args.redis_url)

    count = 0
    batch = []
    for raw_record in dataset:
        batch.append(normalize_hotpot_record(raw_record, subset=args.subset, split=args.split))
        if len(batch) >= 100:
            count += repository.store_samples(batch)
            batch = []
        if args.limit and count + len(batch) >= args.limit:
            break

    if batch:
        remaining = args.limit - count if args.limit else len(batch)
        count += repository.store_samples(batch[:remaining])

    print(f"Imported {count} samples into Redis from {args.subset}/{args.split}")


if __name__ == "__main__":
    main()
