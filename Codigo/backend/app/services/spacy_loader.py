"""Lazy singleton para o modelo spaCy.

Carrega `pt_core_news_lg` na primeira chamada e mantém em memória do processo.
Modelo é pesado (~500MB) e a inicialização demora segundos — não reinstanciar.
"""
import logging
from threading import Lock

import spacy

logger = logging.getLogger(__name__)

_MODEL_NAME = "pt_core_news_lg"
_nlp = None
_lock = Lock()


def get_nlp():
    """Retorna a instância carregada do modelo, carregando-a no primeiro uso."""
    global _nlp
    if _nlp is None:
        with _lock:
            if _nlp is None:
                logger.info("Loading spaCy model %s (first call)", _MODEL_NAME)
                _nlp = spacy.load(_MODEL_NAME)
                logger.info("spaCy model loaded")
    return _nlp
