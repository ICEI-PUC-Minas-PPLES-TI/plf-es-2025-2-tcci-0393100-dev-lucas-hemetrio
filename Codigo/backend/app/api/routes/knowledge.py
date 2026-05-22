"""Rotas do grafo de conhecimento."""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from neomodel import db

from app.api.deps import get_current_user
from app.models.project import Project, ProjectKnowledgeStatus
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeEdgeOut,
    KnowledgeGraphResponse,
    KnowledgeNodeOut,
)
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
        MATCH (p:Project {uid: $uid})-[:HAS_KNOWLEDGE_NODE]->(a:KnowledgeNode)
              -[r:CO_OCCURS_WITH]->(b:KnowledgeNode)
        WHERE a.uid < b.uid
        RETURN a.uid, b.uid, r.weight
        ORDER BY r.weight DESC
        LIMIT $limit
        """,
        {"uid": project_uid, "limit": _EDGE_LIMIT},
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


@router.post("/{project_uid}/rebuild-knowledge", status_code=202)
def post_rebuild_knowledge(
    project_uid: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)
    background_tasks.add_task(rebuild_project_knowledge, project.uid)
    return {"status": "accepted"}
