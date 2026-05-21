import logging

from neomodel import db

logger = logging.getLogger(__name__)

_CREATE_INDEX = """
CREATE FULLTEXT INDEX cognita_search IF NOT EXISTS
FOR (n:Document|DocumentPage|Annotation)
ON EACH [n.title, n.text, n.content, n.extracted_text]
"""


def ensure_search_index() -> None:
    """Cria o índice fulltext usado pela busca global se ele ainda não existir.

    Idempotente. Falhas são logadas mas não interrompem o startup.
    """
    try:
        db.cypher_query(_CREATE_INDEX)
        logger.info("Fulltext index 'cognita_search' garantido.")
    except Exception as exc:  # noqa: BLE001 — startup não pode quebrar por isso
        logger.warning("Falha ao criar índice 'cognita_search': %s", exc)
