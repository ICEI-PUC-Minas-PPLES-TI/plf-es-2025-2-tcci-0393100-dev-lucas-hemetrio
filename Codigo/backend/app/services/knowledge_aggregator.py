"""Acumulador puro do grafo de conhecimento.

Recebe lista de fontes (text, origin_kind, origin_uid) e devolve dicts in-memory
prontos para serem persistidos no Neo4j. Sem dependência de banco.
"""
from collections import defaultdict
from itertools import combinations

from app.services.knowledge_extractor import extract_from_text

# A identidade do nó é o nome normalizado (text_norm). O rótulo NÃO entra na
# chave: o mesmo nome marcado ora como LOC ora como ORG pelo NER instável deve
# ser UM nó só. O rótulo final é o mais frequente entre as menções.
NodeKey = str
EdgeKey = tuple[NodeKey, NodeKey]


def _resolve_label(label_counts: dict[str, int]) -> str:
    """Rótulo dominante: maior contagem; empate decidido pelo nome do rótulo."""
    return max(label_counts.items(), key=lambda kv: (kv[1], kv[0]))[0]


def aggregate_sources(
    sources: list[tuple[str, str, str]],
    nlp,
) -> tuple[dict[NodeKey, dict], list[dict], dict[EdgeKey, int]]:
    """Agrega NER + co-ocorrência sobre múltiplas fontes.

    Co-ocorrência: por sentença em páginas; por anotação inteira em anotações
    (uma nota é uma ideia — entidades nela devem conectar mesmo em sentenças
    diferentes, sem depender da segmentação frágil do spaCy em texto de OCR/HCR).

    Returns:
        (nodes, mentions, edges) — nó indexado por text_norm.
    """
    nodes: dict[NodeKey, dict] = {}
    label_counts: dict[NodeKey, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    mentions: list[dict] = []
    edges: dict[EdgeKey, int] = defaultdict(int)

    for text, origin_kind, origin_uid in sources:
        if not text or not text.strip():
            continue
        is_annotation = origin_kind == "annotation"
        keys_in_source: set[NodeKey] = set()
        sentences = extract_from_text(text, nlp)
        for sent in sentences:
            keys_in_sentence: set[NodeKey] = set()
            for ent in sent.entities:
                key: NodeKey = ent.text_norm
                if key not in nodes:
                    nodes[key] = {
                        "label": ent.label,  # provisório; resolvido no fim
                        "text_norm": ent.text_norm,
                        "text_display": ent.text_display,
                        "mention_count": 0,
                    }
                nodes[key]["mention_count"] += 1
                label_counts[key][ent.label] += 1
                mentions.append({
                    "key": key,
                    "sentence_idx": sent.sentence_idx,
                    "sentence_text": sent.sentence_text,
                    "surface_text": ent.surface_text,
                    "origin_kind": origin_kind,
                    "origin_uid": origin_uid,
                })
                keys_in_sentence.add(key)
                keys_in_source.add(key)
            # páginas co-ocorrem por sentença; anotações no fim, pela fonte inteira
            if not is_annotation:
                for a, b in combinations(sorted(keys_in_sentence), 2):
                    edges[(a, b)] += 1
        if is_annotation:
            for a, b in combinations(sorted(keys_in_source), 2):
                edges[(a, b)] += 1

    for key, data in nodes.items():
        data["label"] = _resolve_label(label_counts[key])

    return nodes, mentions, dict(edges)
