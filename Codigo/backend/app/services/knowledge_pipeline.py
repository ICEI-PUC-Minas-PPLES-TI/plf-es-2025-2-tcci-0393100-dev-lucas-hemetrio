"""Thin orchestrator do rebuild do grafo de conhecimento.

Carrega o projeto, itera fontes via neomodel, chama o aggregator puro, escreve
resultado no Neo4j e gerencia status. Nunca propaga exceções.
"""
import logging
from datetime import datetime, timezone

from app.models.annotation import AnnotationStatus
from app.models.document import DocumentStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.mention import Mention
from app.models.project import Project, ProjectKnowledgeStatus
from app.services.knowledge_aggregator import aggregate_sources
from app.services.spacy_loader import get_nlp

logger = logging.getLogger(__name__)


def _utc_now():
    return datetime.now(timezone.utc)


def _load_project(project_uid: str) -> Project | None:
    return Project.nodes.get_or_none(uid=project_uid)


def _delete_existing(project: Project) -> None:
    """Apaga KnowledgeNode e Mention conectados ao projeto via Cypher direto."""
    from neomodel import db
    db.cypher_query(
        """
        MATCH (p:Project {uid: $uid})-[:HAS_KNOWLEDGE_NODE]->(n:KnowledgeNode)
        OPTIONAL MATCH (m:Mention)-[:OF_ENTITY]->(n)
        DETACH DELETE n, m
        """,
        {"uid": project.uid},
    )


def _iter_sources(project: Project):
    """Yield (text, origin_kind, origin_uid) para cada item INDEXED do projeto."""
    for document in project.documents.all():
        if document.status != DocumentStatus.INDEXED.value:
            continue
        for page in document.pages.all():
            if page.text and page.text.strip():
                yield page.text, "page", page.uid
    for annotation in project.annotations.all():
        if annotation.status != AnnotationStatus.INDEXED.value:
            continue
        if annotation.extracted_text and annotation.extracted_text.strip():
            yield annotation.extracted_text, "annotation", annotation.uid


def _write_graph(project: Project, nodes: dict, mentions: list, edges: dict) -> None:
    """Persiste nodes/mentions/edges no Neo4j. Único escritor da Sprint 7."""
    from app.models.annotation import Annotation
    from app.models.document_page import DocumentPage

    key_to_uid: dict[tuple, str] = {}

    for key, data in nodes.items():
        node = KnowledgeNode(
            label=data["label"],
            text_norm=data["text_norm"],
            text_display=data["text_display"],
            mention_count=data["mention_count"],
        ).save()
        project.knowledge_nodes.connect(node)
        key_to_uid[key] = node.uid

    for spec in mentions:
        entity_node = KnowledgeNode.nodes.get(uid=key_to_uid[spec["key"]])
        mention = Mention(
            sentence_idx=spec["sentence_idx"],
            sentence_text=spec["sentence_text"],
            surface_text=spec["surface_text"],
        ).save()
        mention.entity.connect(entity_node)
        if spec["origin_kind"] == "page":
            origin = DocumentPage.nodes.get_or_none(uid=spec["origin_uid"])
            if origin is not None:
                mention.from_page.connect(origin)
        else:
            origin = Annotation.nodes.get_or_none(uid=spec["origin_uid"])
            if origin is not None:
                mention.from_annotation.connect(origin)

    for (key_a, key_b), weight in edges.items():
        node_a = KnowledgeNode.nodes.get(uid=key_to_uid[key_a])
        node_b = KnowledgeNode.nodes.get(uid=key_to_uid[key_b])
        rel = node_a.co_occurs_with.connect(node_b)
        rel.weight = weight
        rel.save()


def rebuild_project_knowledge(project_uid: str) -> None:
    """Reconstrói o grafo de conhecimento do projeto. Idempotente. Nunca raise."""
    project = _load_project(project_uid)
    if project is None:
        logger.error("rebuild_project_knowledge: project %s not found", project_uid)
        return

    project.knowledge_status = ProjectKnowledgeStatus.PROCESSING
    project.save()

    try:
        _delete_existing(project)
        sources = list(_iter_sources(project))
        nlp = get_nlp()
        nodes, mentions, edges = aggregate_sources(sources, nlp)
        _write_graph(project, nodes, mentions, edges)

        project.knowledge_status = ProjectKnowledgeStatus.DONE
        project.knowledge_updated_at = _utc_now()
        project.save()
        logger.info(
            "rebuild_project_knowledge: project=%s nodes=%d edges=%d mentions=%d",
            project_uid, len(nodes), len(edges), len(mentions),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "rebuild_project_knowledge: project=%s failed: %s", project_uid, exc
        )
        project.knowledge_status = ProjectKnowledgeStatus.FAILED
        project.save()
