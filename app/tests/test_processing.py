from app.core.processing import normalize_hotpot_record, tokenize_text


def test_tokenize_text_keeps_meaningful_tokens_and_normalizes_case():
    tokens = tokenize_text("Who Wrote The River? River bridge bridge")

    assert tokens.count("river") == 2
    assert "who" not in tokens
    assert "wrote" in tokens
    assert "bridge" in tokens


def test_normalize_hotpot_record_builds_structured_context_and_supporting_facts():
    raw_record = {
        "id": "sample-1",
        "question": "Which magazine was started first Arthur's Magazine or First for Women?",
        "answer": "Arthur's Magazine",
        "type": "comparison",
        "level": "medium",
        "context": {
            "title": ["Arthur's Magazine", "First for Women"],
            "sentences": [
                ["Arthur's Magazine was an American literary periodical published in the 19th century."],
                ["First for Women is a woman's magazine published by Bauer Media Group in the USA."],
            ],
        },
        "supporting_facts": {
            "title": ["Arthur's Magazine", "First for Women"],
            "sent_id": [0, 0],
        },
    }

    sample = normalize_hotpot_record(raw_record, subset="distractor", split="validation")

    assert sample.id == "sample-1"
    assert sample.subset == "distractor"
    assert sample.split == "validation"
    assert sample.context_docs[0].title == "Arthur's Magazine"
    assert sample.context_docs[1].sentences[0].startswith("First for Women")
    assert sample.supporting_facts[0].title == "Arthur's Magazine"
    assert sample.supporting_facts[1].sent_id == 0
