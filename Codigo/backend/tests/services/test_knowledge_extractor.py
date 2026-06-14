"""Testes unitários do extractor — sem Neo4j, sem rede.

Modelo spaCy é carregado uma vez por sessão via fixture.
"""
import pytest

from app.services.knowledge_extractor import _normalize, extract_from_text
from app.services.spacy_loader import get_nlp


def test_normalize_folds_accents():
    # "Bioética" e "Bioetica" devem virar a mesma chave de nó no grafo —
    # robustez a erro de digitação/OCR e a anotações sem acento.
    assert _normalize("Bioética") == _normalize("Bioetica")
    assert _normalize("Revista Bioética") == "revista bioetica"


def test_normalize_folds_cedilla_and_tilde():
    assert _normalize("Anotação") == "anotacao"
    assert _normalize("São Paulo") == "sao paulo"


@pytest.fixture(scope="session")
def nlp():
    return get_nlp()


def test_empty_text_returns_empty_list(nlp):
    assert extract_from_text("", nlp) == []


def test_whitespace_only_returns_empty_list(nlp):
    assert extract_from_text("   \n  \t ", nlp) == []


def test_extracts_per_loc_org(nlp):
    text = "Lula visitou o Brasil em nome do governo federal."
    sentences = extract_from_text(text, nlp)
    assert len(sentences) == 1
    labels = {e.label for e in sentences[0].entities}
    assert "PER" in labels
    assert "LOC" in labels or "ORG" in labels


def test_filters_misc_label(nlp):
    text = "O brasileiro Pelé jogou na Copa do Mundo de 1970."
    sentences = extract_from_text(text, nlp)
    for sent in sentences:
        for ent in sent.entities:
            assert ent.label in {"PER", "LOC", "ORG"}


def test_normalization_lowercases_and_strips(nlp):
    text = "BRASIL é grande. Brasil é diverso. brasil tem 200 milhões."
    sentences = extract_from_text(text, nlp)
    all_entities = [e for s in sentences for e in s.entities]
    brasil_norms = {e.text_norm for e in all_entities if "brasil" in e.text_norm}
    assert brasil_norms == {"brasil"}


def test_text_display_preserves_original_form(nlp):
    text = "BRASIL é grande."
    sentences = extract_from_text(text, nlp)
    entities = sentences[0].entities
    brasil = next((e for e in entities if e.text_norm == "brasil"), None)
    if brasil is not None:
        assert brasil.surface_text == "BRASIL"


def test_multiple_sentences_indexed(nlp):
    text = "Lula falou. Bolsonaro respondeu. Dilma estava lá."
    sentences = extract_from_text(text, nlp)
    assert len(sentences) >= 2
    idxs = [s.sentence_idx for s in sentences]
    assert idxs == sorted(idxs)
    assert idxs[0] == 0


def test_short_annotation_without_punctuation(nlp):
    text = "Lula visitou Brasília"
    sentences = extract_from_text(text, nlp)
    assert len(sentences) == 1
    assert sentences[0].sentence_idx == 0
    assert sentences[0].sentence_text.strip() == "Lula visitou Brasília"
