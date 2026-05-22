"""Acumulador puro do grafo de conhecimento.

Recebe lista de fontes (text, origin_kind, origin_uid) e devolve dicts in-memory
prontos para serem persistidos no Neo4j. Sem dependência de banco.
"""
from collections import defaultdict
from itertools import combinations

from app.services.knowledge_extractor import extract_from_text

NodeKey = tuple[str, str]
EdgeKey = tuple[NodeKey, NodeKey]


def aggregate_sources(
    sources: list[tuple[str, str, str]],
    nlp,
) -> tuple[dict[NodeKey, dict], list[dict], dict[EdgeKey, int]]:
    """Agrega NER + co-ocorrência sobre múltiplas fontes.

    Returns:
        (nodes, mentions, edges) — ver docstring no spec/plan.
    """
    nodes: dict[NodeKey, dict] = {}
    mentions: list[dict] = []
    edges: dict[EdgeKey, int] = defaultdict(int)

    for text, origin_kind, origin_uid in sources:
        if not text or not text.strip():
            continue
        sentences = extract_from_text(text, nlp)
        for sent in sentences:
            keys_in_sentence: set[NodeKey] = set()
            for ent in sent.entities:
                key: NodeKey = (ent.label, ent.text_norm)
                if key not in nodes:
                    nodes[key] = {
                        "label": ent.label,
                        "text_norm": ent.text_norm,
                        "text_display": ent.text_display,
                        "mention_count": 0,
                    }
                nodes[key]["mention_count"] += 1
                mentions.append({
                    "key": key,
                    "sentence_idx": sent.sentence_idx,
                    "sentence_text": sent.sentence_text,
                    "surface_text": ent.surface_text,
                    "origin_kind": origin_kind,
                    "origin_uid": origin_uid,
                })
                keys_in_sentence.add(key)
            for a, b in combinations(sorted(keys_in_sentence), 2):
                edges[(a, b)] += 1

    return nodes, mentions, dict(edges)
