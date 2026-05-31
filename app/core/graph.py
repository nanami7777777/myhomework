from __future__ import annotations

from app.core.models import HotpotSample


def build_reasoning_graph(sample: HotpotSample) -> dict:
    nodes = [
        {"id": "question", "kind": "question", "label": sample.question},
        {"id": "answer", "kind": "answer", "label": sample.answer},
    ]
    edges = []

    context_by_title = {context_doc.title: context_doc for context_doc in sample.context_docs}

    for supporting_fact in sample.supporting_facts:
        title_node_id = f"title:{supporting_fact.title}"
        sentence_node_id = f"sentence:{supporting_fact.title}:{supporting_fact.sent_id}"
        context_doc = context_by_title.get(supporting_fact.title)
        sentence = ""
        if context_doc and 0 <= supporting_fact.sent_id < len(context_doc.sentences):
            sentence = context_doc.sentences[supporting_fact.sent_id]

        if not any(node["id"] == title_node_id for node in nodes):
            nodes.append({"id": title_node_id, "kind": "title", "label": supporting_fact.title})
        if not any(node["id"] == sentence_node_id for node in nodes):
            nodes.append({"id": sentence_node_id, "kind": "sentence", "label": sentence})

        edges.append({"source": "question", "target": title_node_id, "kind": "mentions"})
        edges.append({"source": title_node_id, "target": sentence_node_id, "kind": "supports"})
        edges.append({"source": sentence_node_id, "target": "answer", "kind": "leads_to"})

    return {"sample_id": sample.id, "question_type": sample.type, "nodes": nodes, "edges": edges}
