"""Extração de entidades nomeadas (PER/LOC/ORG) por sentença usando spaCy.

Função pura — sem Neo4j, sem efeitos colaterais. Carrega o modelo via spacy_loader.
"""
import unicodedata
from dataclasses import dataclass

_ALLOWED_LABELS = {"PER", "LOC", "ORG"}


@dataclass
class ExtractedEntity:
    label: str
    text_norm: str
    text_display: str
    surface_text: str


@dataclass
class ExtractedSentence:
    sentence_idx: int
    sentence_text: str
    entities: list[ExtractedEntity]


def _normalize(text: str) -> str:
    # Remove diacríticos (acentos/cedilha) para que a chave do nó seja insensível
    # a acento: "Bioética" e "Bioetica" → mesma entidade no grafo. O text_display
    # preserva a forma original; só o text_norm (chave) é dobrado.
    decomposed = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def extract_from_text(text: str, nlp) -> list[ExtractedSentence]:
    """Roda spaCy sobre `text` e retorna entidades agrupadas por sentença.

    - Filtra labels para {PER, LOC, ORG}.
    - Sentenças vêm de `doc.sents` do spaCy.
    - Texto vazio ou só whitespace → lista vazia.
    """
    if not text or not text.strip():
        return []

    doc = nlp(text)
    out: list[ExtractedSentence] = []
    for idx, sent in enumerate(doc.sents):
        entities: list[ExtractedEntity] = []
        for ent in sent.ents:
            if ent.label_ not in _ALLOWED_LABELS:
                continue
            surface = ent.text
            norm = _normalize(surface)
            if not norm:
                continue
            entities.append(
                ExtractedEntity(
                    label=ent.label_,
                    text_norm=norm,
                    text_display=surface,
                    surface_text=surface,
                )
            )
        out.append(
            ExtractedSentence(
                sentence_idx=idx,
                sentence_text=sent.text,
                entities=entities,
            )
        )
    return out
