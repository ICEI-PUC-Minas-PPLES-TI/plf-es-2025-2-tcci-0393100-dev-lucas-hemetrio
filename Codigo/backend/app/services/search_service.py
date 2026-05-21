import re

from neomodel import db

from app.schemas.search import (
    SearchAnnotationHit,
    SearchAnnotationRef,
    SearchDocumentGroup,
    SearchDocumentRef,
    SearchPageHit,
    SearchProjectGroup,
    SearchProjectRef,
    SearchResponse,
    SearchTitleMatch,
)

_LUCENE_SPECIAL = re.compile(r'([+\-!(){}\[\]^"~*?:\\/&|])')


def _escape_lucene(query: str) -> str:
    """Escapa caracteres especiais Lucene para uso seguro em db.index.fulltext.queryNodes."""
    if not query:
        return ""
    return _LUCENE_SPECIAL.sub(r"\\\1", query)


def _make_snippet(text: str, query: str, max_len: int = 150) -> str:
    """Recorta janela de até max_len chars centrada no primeiro match do termo de busca.

    Marca a ocorrência (caso encontrada) com **...** preservando a caixa original.
    Se o termo não aparecer no texto, retorna o prefixo do texto.
    """
    if not text:
        return ""

    tokens = [t for t in query.split() if t]
    if not tokens:
        return text[:max_len] + ("..." if len(text) > max_len else "")

    anchor = tokens[0]
    lower_text = text.lower()
    lower_anchor = anchor.lower()
    idx = lower_text.find(lower_anchor)

    if idx == -1:
        truncated = text[:max_len]
        return truncated + ("..." if len(text) > max_len else "")

    half = (max_len - len(anchor)) // 2
    start = max(0, idx - half)
    end = min(len(text), start + max_len)
    start = max(0, end - max_len)

    original_match = text[idx : idx + len(anchor)]
    marked = (
        text[start:idx]
        + f"**{original_match}**"
        + text[idx + len(anchor) : end]
    )

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return prefix + marked + suffix


_DOC_QUERY = """
CALL db.index.fulltext.queryNodes('cognita_search', $q) YIELD node, score
WHERE (node:Document OR node:DocumentPage)
MATCH (u:User {uid:$user_uid})-[:has]->(p:Project)-[:CONTAINS]->(d:Document)
WHERE (node = d) OR ((d)-[:HAS_PAGE]->(node))
WITH p, d, node, score WHERE d.status = 'INDEXED'
RETURN p, d, node, score, labels(node) AS lbl
ORDER BY score DESC LIMIT 50
"""

_ANN_QUERY = """
CALL db.index.fulltext.queryNodes('cognita_search', $q) YIELD node, score
WHERE node:Annotation AND node.status = 'INDEXED'
MATCH (u:User {uid:$user_uid})-[:has]->(p:Project)-[:CONTAINS]->(node)
OPTIONAL MATCH (d:Document)-[:CONTAINS]->(node)
RETURN p, d, node, score
ORDER BY score DESC LIMIT 50
"""


def _node_props(node):
    if node is None:
        return None
    if hasattr(node, "_properties"):
        return dict(node._properties)
    return dict(node)


def _run_doc_query(escaped_query: str, user_uid: str):
    """Executa a query Cypher de Documents+Pages. Retorna lista de tuplas (p, d, node, score, lbl)."""
    results, _ = db.cypher_query(
        _DOC_QUERY,
        {"q": escaped_query, "user_uid": user_uid},
        resolve_objects=False,
    )
    return [
        (_node_props(row[0]), _node_props(row[1]), _node_props(row[2]), float(row[3]), list(row[4]))
        for row in results
    ]


def _run_annotation_query(escaped_query: str, user_uid: str):
    """Executa a query Cypher de Annotations. Retorna lista de tuplas (p, d|None, node, score)."""
    results, _ = db.cypher_query(
        _ANN_QUERY,
        {"q": escaped_query, "user_uid": user_uid},
        resolve_objects=False,
    )
    return [
        (_node_props(row[0]), _node_props(row[1]), _node_props(row[2]), float(row[3]))
        for row in results
    ]


def search(user_uid: str, query: str, limit: int = 50) -> SearchResponse:
    """Busca global por texto em documentos e anotações do usuário.

    Levanta ValueError se a query tiver menos de 2 chars não-whitespace.
    """
    cleaned = (query or "").strip()
    if len(cleaned) < 2:
        raise ValueError("Query must have at least 2 non-whitespace characters")

    escaped = _escape_lucene(cleaned)

    doc_rows = _run_doc_query(escaped, user_uid)
    ann_rows = _run_annotation_query(escaped, user_uid)

    projects: dict[str, dict] = {}

    def _project_bucket(p):
        bucket = projects.get(p["uid"])
        if bucket is None:
            bucket = {
                "project": SearchProjectRef(uid=p["uid"], name=p.get("name", "")),
                "documents": {},
                "annotations": [],
                "best_score": 0.0,
            }
            projects[p["uid"]] = bucket
        return bucket

    combined = []
    for p, d, node, score, lbl in doc_rows:
        combined.append(("doc_or_page", score, p, d, node, lbl))
    for p, d, node, score in ann_rows:
        combined.append(("annotation", score, p, d, node, None))
    combined.sort(key=lambda r: r[1], reverse=True)
    combined = combined[:limit]

    for kind, score, p, d, node, lbl in combined:
        bucket = _project_bucket(p)
        bucket["best_score"] = max(bucket["best_score"], score)

        if kind == "annotation":
            text = node.get("extracted_text") or node.get("content") or node.get("title", "")
            bucket["annotations"].append(
                SearchAnnotationHit(
                    annotation=SearchAnnotationRef(uid=node["uid"], title=node.get("title", "")),
                    snippet=_make_snippet(text, cleaned),
                    score=score,
                )
            )
            continue

        doc_bucket = bucket["documents"].get(d["uid"])
        if doc_bucket is None:
            doc_bucket = {
                "document": SearchDocumentRef(uid=d["uid"], title=d.get("title", "")),
                "title_match": None,
                "page_hits": [],
            }
            bucket["documents"][d["uid"]] = doc_bucket

        if lbl and "Document" in lbl and node["uid"] == d["uid"]:
            doc_bucket["title_match"] = SearchTitleMatch(
                snippet=_make_snippet(d.get("title", ""), cleaned)
            )
        else:
            doc_bucket["page_hits"].append(
                SearchPageHit(
                    page_number=int(node.get("page_number", 0)),
                    snippet=_make_snippet(node.get("text", ""), cleaned),
                    score=score,
                )
            )

    project_groups = []
    for bucket in sorted(projects.values(), key=lambda b: b["best_score"], reverse=True):
        project_groups.append(
            SearchProjectGroup(
                project=bucket["project"],
                documents=[
                    SearchDocumentGroup(
                        document=db_["document"],
                        title_match=db_["title_match"],
                        page_hits=db_["page_hits"],
                    )
                    for db_ in bucket["documents"].values()
                ],
                annotations=bucket["annotations"],
            )
        )

    return SearchResponse(
        query=cleaned,
        total=len(combined),
        results_by_project=project_groups,
    )
