"""Formatadores puros para respostas de menções/co-ocorrências.

Mantido isolado do acesso a DB para permitir TDD sem Neo4j (convenção do projeto).
"""
from typing import Any


_FALLBACK_TITLE = "(sem título)"


def format_mention_row(row: tuple, include_uid: bool = True) -> dict[str, Any]:
    """Converte uma tupla retornada pelo Cypher em dict do schema.

    Layout esperado da tupla:
        (mention_uid, sentence_text, source_type, source_uid, source_title, page_number)

    `mention_uid` é ignorado quando `include_uid=False` (usado pelo endpoint de
    co-occurrences, que não expõe identidade da menção individual).
    """
    mention_uid, sentence_text, source_type, source_uid, source_title, page_number = row
    out: dict[str, Any] = {
        "sentence_text": sentence_text,
        "source_type": source_type,
        "source_uid": source_uid,
        "source_title": source_title or _FALLBACK_TITLE,
        "page_number": page_number,
    }
    if include_uid:
        out["uid"] = mention_uid
    return out
