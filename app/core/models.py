from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ContextDoc:
    title: str
    sentences: list[str] = field(default_factory=list)


@dataclass
class SupportingFact:
    title: str
    sent_id: int


@dataclass
class HotpotSample:
    id: str
    subset: str
    split: str
    question: str
    answer: str
    type: str
    level: str
    context_docs: list[ContextDoc] = field(default_factory=list)
    supporting_facts: list[SupportingFact] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
