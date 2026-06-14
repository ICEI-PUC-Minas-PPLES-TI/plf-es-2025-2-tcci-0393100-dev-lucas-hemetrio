"""Testes do aggregator puro. Sem Neo4j, sem rede."""
from unittest.mock import patch

import pytest

from app.services.knowledge_aggregator import aggregate_sources
from app.services.knowledge_extractor import ExtractedEntity, ExtractedSentence
from app.services.spacy_loader import get_nlp


@pytest.fixture(scope="session")
def nlp():
    return get_nlp()


def _sent(idx, ents):
    """ExtractedSentence com entidades controladas: ents = [(label, norm, display)]."""
    return ExtractedSentence(
        sentence_idx=idx,
        sentence_text=f"s{idx}",
        entities=[
            ExtractedEntity(label=l, text_norm=n, text_display=d, surface_text=d)
            for l, n, d in ents
        ],
    )


def test_same_name_different_labels_merge_into_one_node():
    # NER instável marca a mesma entidade como LOC numa fonte e ORG noutra; devem
    # virar UM nó só — identidade por nome (text_norm), não por rótulo.
    def fake_extract(text, _nlp):
        if text == "ann":
            return [_sent(0, [("LOC", "revista bioetica", "Revista Bioetica")])]
        return [_sent(0, [("ORG", "revista bioetica", "Revista Bioética")])]

    with patch(
        "app.services.knowledge_aggregator.extract_from_text", side_effect=fake_extract
    ):
        nodes, mentions, _ = aggregate_sources(
            [("ann", "annotation", "ann-1"), ("pg", "page", "pg-1")], nlp=None
        )

    assert len(nodes) == 1
    key = next(iter(nodes))
    assert nodes[key]["mention_count"] == 2


def test_merged_node_uses_dominant_label():
    # Rótulo do nó mesclado = o mais frequente entre as menções (2 ORG vs 1 LOC).
    def fake_extract(text, _nlp):
        label = "LOC" if text == "src0" else "ORG"
        return [_sent(0, [(label, "x", "X")])]

    with patch(
        "app.services.knowledge_aggregator.extract_from_text", side_effect=fake_extract
    ):
        nodes, _, _ = aggregate_sources(
            [("src0", "page", "p"), ("src1", "page", "p"), ("src2", "page", "p")],
            nlp=None,
        )

    key = next(iter(nodes))
    assert nodes[key]["label"] == "ORG"


def test_annotation_cooccurs_across_sentences():
    # Numa anotação (nota = uma ideia), entidades em sentenças diferentes ainda
    # co-ocorrem — não dependem da segmentação frágil do spaCy.
    def fake_extract(text, _nlp):
        return [_sent(0, [("LOC", "a", "A")]), _sent(1, [("LOC", "b", "B")])]

    with patch(
        "app.services.knowledge_aggregator.extract_from_text", side_effect=fake_extract
    ):
        _, _, edges = aggregate_sources([("t", "annotation", "ann-1")], nlp=None)

    assert ("a", "b") in edges


def test_page_does_not_cooccur_across_sentences():
    # Página continua por sentença: entidades em sentenças diferentes NÃO conectam.
    def fake_extract(text, _nlp):
        return [_sent(0, [("LOC", "a", "A")]), _sent(1, [("LOC", "b", "B")])]

    with patch(
        "app.services.knowledge_aggregator.extract_from_text", side_effect=fake_extract
    ):
        _, _, edges = aggregate_sources([("t", "page", "pg-1")], nlp=None)

    assert edges == {}


def test_aggregate_empty_sources(nlp):
    nodes, mentions, edges = aggregate_sources([], nlp)
    assert nodes == {}
    assert mentions == []
    assert edges == {}


def test_aggregate_one_sentence_two_entities(nlp):
    sources = [("Lula visitou o Brasil ontem.", "page", "pg-1")]
    nodes, mentions, edges = aggregate_sources(sources, nlp)
    assert len(nodes) >= 2
    assert any(w == 1 for w in edges.values())
    assert len(mentions) >= 2
    assert all(m["origin_kind"] == "page" for m in mentions)
    assert all(m["origin_uid"] == "pg-1" for m in mentions)


def test_edge_weight_accumulates_across_sentences(nlp):
    text = (
        "Lula visitou o Brasil em janeiro. "
        "Lula também visitou o Brasil em março. "
        "Em abril, Lula esteve no Brasil."
    )
    sources = [(text, "page", "pg-1")]
    nodes, mentions, edges = aggregate_sources(sources, nlp)

    lula_key = next(k for k in nodes if k == "lula")
    brasil_key = next(k for k in nodes if "brasil" in k)
    edge_key = tuple(sorted([lula_key, brasil_key]))
    assert edges[edge_key] == 3


def test_mention_count_reflects_occurrences(nlp):
    text = "Lula falou. Lula respondeu. Bolsonaro também."
    sources = [(text, "page", "pg-1")]
    nodes, _, _ = aggregate_sources(sources, nlp)
    lula_key = next(k for k in nodes if k == "lula")
    assert nodes[lula_key]["mention_count"] == 2


def test_annotation_origin_is_preserved(nlp):
    sources = [("Lula visitou Brasília", "annotation", "ann-1")]
    _, mentions, _ = aggregate_sources(sources, nlp)
    assert all(m["origin_kind"] == "annotation" for m in mentions)
    assert all(m["origin_uid"] == "ann-1" for m in mentions)


def test_multiple_sources_share_nodes(nlp):
    """Mesma entidade em fontes diferentes deve agregar mentions no mesmo nó."""
    sources = [
        ("Lula visitou o Brasil em janeiro.", "page", "pg-1"),
        ("Lula esteve no Brasil em março.", "annotation", "ann-1"),
    ]
    nodes, mentions, _ = aggregate_sources(sources, nlp)
    lula_key = next(k for k in nodes if k == "lula")
    lula_mentions = [m for m in mentions if m["key"] == lula_key]
    assert len(lula_mentions) == 2
    assert {m["origin_kind"] for m in lula_mentions} == {"page", "annotation"}


def test_dedup_same_entity_repeated_in_sentence(nlp):
    text = "Lula encontrou Lula no Brasil."
    sources = [(text, "page", "pg-1")]
    nodes, _, edges = aggregate_sources(sources, nlp)
    if nodes:
        for (a, b) in edges:
            assert a != b


def test_empty_text_in_source_is_skipped(nlp):
    sources = [
        ("   ", "page", "pg-1"),
        ("Lula está no Brasil.", "page", "pg-2"),
    ]
    nodes, mentions, _ = aggregate_sources(sources, nlp)
    assert all(m["origin_uid"] == "pg-2" for m in mentions)
    assert len(nodes) >= 1
