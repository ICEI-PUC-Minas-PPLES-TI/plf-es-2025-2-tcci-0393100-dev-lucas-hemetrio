"""Rotas do grafo de conhecimento."""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from neomodel import db

from app.api.deps import get_current_user
from app.models.project import Project, ProjectKnowledgeStatus
from app.models.user import User
from app.schemas.knowledge import (
    CoOccurrenceOut,
    CoOccurrencesResponse,
    KnowledgeEdgeOut,
    KnowledgeGraphResponse,
    KnowledgeNodeOut,
    MentionOut,
    MentionsListResponse,
)
from app.services.knowledge_mentions import format_mention_row
from app.services.knowledge_pipeline import rebuild_project_knowledge

logger = logging.getLogger(__name__)
router = APIRouter()

_NODE_LIMIT = 500
_EDGE_LIMIT = 2000


def _get_owned_project(current_user: User, project_uid: str) -> Project:
    """Mesmo padrão de app/api/routes/projects.py._get_owned_project."""
    project = next(
        (item for item in current_user.projects.all() if item.uid == project_uid),
        None,
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def _query_nodes(project_uid: str) -> list:
    result, _ = db.cypher_query(
        """
        MATCH (p:Project {uid: $uid})-[:HAS_KNOWLEDGE_NODE]->(n:KnowledgeNode)
        RETURN n.uid, n.label, n.text_display, n.mention_count
        ORDER BY n.mention_count DESC
        LIMIT $limit
        """,
        {"uid": project_uid, "limit": _NODE_LIMIT},
    )
    return result


def _query_edges(project_uid: str) -> list:
    result, _ = db.cypher_query(
        """
        MATCH (p:Project {uid: $uid})-[:HAS_KNOWLEDGE_NODE]->(a:KnowledgeNode),
              (p)-[:HAS_KNOWLEDGE_NODE]->(b:KnowledgeNode),
              (a)-[r:CO_OCCURS_WITH]-(b)
        WHERE a.uid < b.uid
        RETURN a.uid, b.uid, r.weight
        ORDER BY r.weight DESC
        LIMIT $limit
        """,
        {"uid": project_uid, "limit": _EDGE_LIMIT},
    )
    return result


def _query_node_summary(project_uid: str, node_uid: str):
    """Retorna (uid, label, text_display, mention_count) ou None se nó não pertence ao projeto."""
    result, _ = db.cypher_query(
        """
        MATCH (p:Project {uid: $project_uid})-[:HAS_KNOWLEDGE_NODE]->(n:KnowledgeNode {uid: $node_uid})
        RETURN n.uid, n.label, n.text_display, n.mention_count
        LIMIT 1
        """,
        {"project_uid": project_uid, "node_uid": node_uid},
    )
    return result[0] if result else None


def _query_mentions_by_node(project_uid: str, node_uid: str) -> list:
    """Retorna lista de tuplas (mention_uid, sentence_text, source_type, source_uid, source_title, page_number)."""
    result, _ = db.cypher_query(
        """
        MATCH (p:Project {uid: $project_uid})-[:HAS_KNOWLEDGE_NODE]->(n:KnowledgeNode {uid: $node_uid})
        CALL {
          WITH n
          MATCH (n)<-[:OF_ENTITY]-(m:Mention)-[:FROM_PAGE]->(pg:DocumentPage)<-[:HAS_PAGE]-(d:Document)
          RETURN m.uid AS mention_uid, m.sentence_text AS sentence_text,
                 'document' AS source_type, d.uid AS source_uid,
                 d.title AS source_title, pg.page_number AS page_number
          UNION ALL
          WITH n
          MATCH (n)<-[:OF_ENTITY]-(m:Mention)-[:FROM_ANNOTATION]->(a:Annotation)
          RETURN m.uid AS mention_uid, m.sentence_text AS sentence_text,
                 'annotation' AS source_type, a.uid AS source_uid,
                 a.title AS source_title, null AS page_number
        }
        RETURN mention_uid, sentence_text, source_type, source_uid, source_title, page_number
        ORDER BY source_type ASC, source_title ASC, coalesce(page_number, 0) ASC
        """,
        {"project_uid": project_uid, "node_uid": node_uid},
    )
    return result


@router.get("/{project_uid}/knowledge-graph")
def get_knowledge_graph(
    project_uid: str,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)

    if project.knowledge_status == ProjectKnowledgeStatus.PROCESSING:
        return JSONResponse(
            status_code=202,
            content={
                "status": "PROCESSING",
                "updated_at": None,
                "nodes": [],
                "edges": [],
            },
        )

    if project.knowledge_status in (
        ProjectKnowledgeStatus.IDLE,
        ProjectKnowledgeStatus.FAILED,
    ):
        return KnowledgeGraphResponse(
            status=project.knowledge_status,
            updated_at=project.knowledge_updated_at,
            nodes=[],
            edges=[],
        ).model_dump(mode="json")

    nodes_result = _query_nodes(project.uid)
    nodes = [
        KnowledgeNodeOut(uid=row[0], label=row[1], text=row[2], mention_count=row[3])
        for row in nodes_result
    ]
    node_uids = {n.uid for n in nodes}

    edges_result = _query_edges(project.uid)
    edges = [
        KnowledgeEdgeOut(source=row[0], target=row[1], weight=row[2])
        for row in edges_result
        if row[0] in node_uids and row[1] in node_uids
    ]

    return KnowledgeGraphResponse(
        status=ProjectKnowledgeStatus.DONE,
        updated_at=project.knowledge_updated_at,
        nodes=nodes,
        edges=edges,
    ).model_dump(mode="json")


def _query_edge_summary(project_uid: str, a_uid: str, b_uid: str):
    """Retorna ((a_uid, label, text, count), (b_uid, ...), weight) ou None.

    Caller já passou (a,b) em ordem canônica (a < b).
    """
    result, _ = db.cypher_query(
        """
        MATCH (p:Project {uid: $project_uid})-[:HAS_KNOWLEDGE_NODE]->(a:KnowledgeNode {uid: $a_uid}),
              (p)-[:HAS_KNOWLEDGE_NODE]->(b:KnowledgeNode {uid: $b_uid}),
              (a)-[r:CO_OCCURS_WITH]-(b)
        RETURN a.uid, a.label, a.text_display, a.mention_count,
               b.uid, b.label, b.text_display, b.mention_count,
               r.weight
        LIMIT 1
        """,
        {"project_uid": project_uid, "a_uid": a_uid, "b_uid": b_uid},
    )
    if not result:
        return None
    row = result[0]
    return (
        (row[0], row[1], row[2], row[3]),
        (row[4], row[5], row[6], row[7]),
        row[8],
    )


def _query_co_occurrences(project_uid: str, a_uid: str, b_uid: str) -> list:
    """Sentenças onde a e b co-ocorrem (mesma origem + mesmo sentence_idx)."""
    result, _ = db.cypher_query(
        """
        MATCH (p:Project {uid: $project_uid})-[:HAS_KNOWLEDGE_NODE]->(a:KnowledgeNode {uid: $a_uid}),
              (p)-[:HAS_KNOWLEDGE_NODE]->(b:KnowledgeNode {uid: $b_uid})
        CALL {
          WITH a, b
          MATCH (a)<-[:OF_ENTITY]-(ma:Mention)-[:FROM_PAGE]->(pg:DocumentPage)<-[:HAS_PAGE]-(d:Document),
                (b)<-[:OF_ENTITY]-(mb:Mention)-[:FROM_PAGE]->(pg)
          WHERE ma.sentence_idx = mb.sentence_idx
          RETURN DISTINCT ma.sentence_text AS sentence_text,
                 'document' AS source_type, d.uid AS source_uid,
                 d.title AS source_title, pg.page_number AS page_number
          UNION ALL
          WITH a, b
          MATCH (a)<-[:OF_ENTITY]-(ma:Mention)-[:FROM_ANNOTATION]->(an:Annotation),
                (b)<-[:OF_ENTITY]-(mb:Mention)-[:FROM_ANNOTATION]->(an)
          WHERE ma.sentence_idx = mb.sentence_idx
          RETURN DISTINCT ma.sentence_text AS sentence_text,
                 'annotation' AS source_type, an.uid AS source_uid,
                 an.title AS source_title, null AS page_number
        }
        RETURN null AS mention_uid, sentence_text, source_type, source_uid, source_title, page_number
        ORDER BY source_type ASC, source_title ASC, coalesce(page_number, 0) ASC
        """,
        {"project_uid": project_uid, "a_uid": a_uid, "b_uid": b_uid},
    )
    return result


@router.get("/{project_uid}/knowledge-graph/nodes/{node_uid}/mentions")
def get_node_mentions(
    project_uid: str,
    node_uid: str,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)
    summary = _query_node_summary(project.uid, node_uid)
    if summary is None:
        raise HTTPException(status_code=404, detail="Node not found")

    node = KnowledgeNodeOut(
        uid=summary[0], label=summary[1], text=summary[2], mention_count=summary[3],
    )
    rows = _query_mentions_by_node(project.uid, node_uid)
    mentions = [MentionOut(**format_mention_row(row)) for row in rows]
    return MentionsListResponse(node=node, mentions=mentions).model_dump(mode="json")


@router.get("/{project_uid}/knowledge-graph/edges/{a_uid}/{b_uid}/co-occurrences")
def get_edge_co_occurrences(
    project_uid: str,
    a_uid: str,
    b_uid: str,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)

    # Ordem canônica (a < b), igual à Sprint 7.
    if a_uid > b_uid:
        a_uid, b_uid = b_uid, a_uid

    summary = _query_edge_summary(project.uid, a_uid, b_uid)
    if summary is None:
        raise HTTPException(status_code=404, detail="Edge not found")

    a_tuple, b_tuple, weight = summary
    node_a = KnowledgeNodeOut(
        uid=a_tuple[0], label=a_tuple[1], text=a_tuple[2], mention_count=a_tuple[3],
    )
    node_b = KnowledgeNodeOut(
        uid=b_tuple[0], label=b_tuple[1], text=b_tuple[2], mention_count=b_tuple[3],
    )

    rows = _query_co_occurrences(project.uid, a_uid, b_uid)
    co_occurrences = [
        CoOccurrenceOut(**format_mention_row(row, include_uid=False))
        for row in rows
    ]

    return CoOccurrencesResponse(
        node_a=node_a, node_b=node_b, weight=weight, co_occurrences=co_occurrences,
    ).model_dump(mode="json")


@router.post("/{project_uid}/rebuild-knowledge", status_code=202)
def post_rebuild_knowledge(
    project_uid: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)
    background_tasks.add_task(rebuild_project_knowledge, project.uid)
    return {"status": "accepted"}
