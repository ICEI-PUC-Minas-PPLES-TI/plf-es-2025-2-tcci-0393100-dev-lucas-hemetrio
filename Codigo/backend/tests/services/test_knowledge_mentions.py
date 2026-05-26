"""Testes da função pura format_mention_row — sem Neo4j."""
from app.services.knowledge_mentions import format_mention_row


def test_format_row_document_with_page():
    row = (
        "m-uid-1",
        "Beauchamp e Childress propuseram quatro princípios.",
        "document",
        "doc-uid-1",
        "Bioética - Cap 1",
        3,
    )
    out = format_mention_row(row)
    assert out == {
        "uid": "m-uid-1",
        "sentence_text": "Beauchamp e Childress propuseram quatro princípios.",
        "source_type": "document",
        "source_uid": "doc-uid-1",
        "source_title": "Bioética - Cap 1",
        "page_number": 3,
    }


def test_format_row_annotation_no_page():
    row = (
        "m-uid-2",
        "Anotação curta sobre Beauchamp.",
        "annotation",
        "ann-uid-1",
        "Anotação 2",
        None,
    )
    out = format_mention_row(row)
    assert out["source_type"] == "annotation"
    assert out["page_number"] is None
    assert out["source_title"] == "Anotação 2"


def test_format_row_with_null_title_falls_back():
    row = (
        "m-uid-3",
        "Frase qualquer.",
        "document",
        "doc-uid-2",
        None,
        7,
    )
    out = format_mention_row(row)
    assert out["source_title"] == "(sem título)"


def test_format_row_drops_uid_when_omitted():
    # Variante usada pelo endpoint de co-occurrences (sem mention uid).
    row = (
        None,
        "Frase de co-ocorrência.",
        "document",
        "doc-uid-3",
        "Outro Doc",
        2,
    )
    out = format_mention_row(row, include_uid=False)
    assert "uid" not in out
    assert out["sentence_text"] == "Frase de co-ocorrência."
