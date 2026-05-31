from __future__ import annotations

import re
from collections.abc import Iterable

from app.core.models import ContextDoc, HotpotSample, SupportingFact

TOKEN_PATTERN = re.compile(r"[a-z0-9']+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "what",
    "when",
    "which",
    "who",
    "with",
}


def tokenize_text(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


def _paired_docs(titles: Iterable[str], sentences: Iterable[list[str]]) -> list[ContextDoc]:
    return [
        ContextDoc(title=title, sentences=list(sentence_list))
        for title, sentence_list in zip(titles, sentences)
    ]


def _paired_supporting_facts(titles: Iterable[str], sent_ids: Iterable[int]) -> list[SupportingFact]:
    return [SupportingFact(title=title, sent_id=int(sent_id)) for title, sent_id in zip(titles, sent_ids)]


def normalize_hotpot_record(raw_record: dict, *, subset: str, split: str) -> HotpotSample:
    context = raw_record.get("context", {})
    supporting_facts = raw_record.get("supporting_facts", {})

    return HotpotSample(
        id=str(raw_record.get("id", "")),
        subset=subset,
        split=split,
        question=str(raw_record.get("question", "")),
        answer=str(raw_record.get("answer", "")),
        type=str(raw_record.get("type", "")),
        level=str(raw_record.get("level", "")),
        context_docs=_paired_docs(context.get("title", []), context.get("sentences", [])),
        supporting_facts=_paired_supporting_facts(
            supporting_facts.get("title", []), supporting_facts.get("sent_id", [])
        ),
    )


def searchable_text(sample: HotpotSample) -> str:
    pieces = [sample.question, sample.answer]
    for context_doc in sample.context_docs:
        pieces.append(context_doc.title)
        pieces.extend(context_doc.sentences)
    return " ".join(pieces)
