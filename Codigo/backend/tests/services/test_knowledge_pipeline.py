"""Testes do orquestrador. Tudo que toca Neo4j é mockado."""
from unittest.mock import MagicMock, patch

from app.services.knowledge_pipeline import rebuild_project_knowledge


def _make_project_mock(uid="p-1"):
    p = MagicMock()
    p.uid = uid
    p.knowledge_status = "IDLE"
    return p


def test_returns_silently_when_project_missing():
    with patch(
        "app.services.knowledge_pipeline._load_project", return_value=None
    ):
        rebuild_project_knowledge("ghost-uid")


def test_sets_status_done_on_empty_project():
    project = _make_project_mock()
    with patch("app.services.knowledge_pipeline._load_project", return_value=project), \
         patch("app.services.knowledge_pipeline._delete_existing"), \
         patch("app.services.knowledge_pipeline._iter_sources", return_value=[]), \
         patch("app.services.knowledge_pipeline.get_nlp"), \
         patch("app.services.knowledge_pipeline.aggregate_sources",
               return_value=({}, [], {})), \
         patch("app.services.knowledge_pipeline._write_graph") as write:
        rebuild_project_knowledge(project.uid)

    assert project.knowledge_status == "DONE"
    project.save.assert_called()
    write.assert_called_once()


def test_sets_status_failed_on_exception():
    project = _make_project_mock()
    with patch("app.services.knowledge_pipeline._load_project", return_value=project), \
         patch("app.services.knowledge_pipeline._delete_existing",
               side_effect=RuntimeError("boom")):
        rebuild_project_knowledge(project.uid)

    assert project.knowledge_status == "FAILED"


def test_calls_aggregate_with_iterated_sources():
    project = _make_project_mock()
    fake_sources = [("texto 1", "page", "pg-1"), ("texto 2", "annotation", "ann-1")]

    with patch("app.services.knowledge_pipeline._load_project", return_value=project), \
         patch("app.services.knowledge_pipeline._delete_existing"), \
         patch("app.services.knowledge_pipeline._iter_sources", return_value=fake_sources), \
         patch("app.services.knowledge_pipeline.get_nlp", return_value="NLP"), \
         patch("app.services.knowledge_pipeline.aggregate_sources",
               return_value=({}, [], {})) as agg, \
         patch("app.services.knowledge_pipeline._write_graph"):
        rebuild_project_knowledge(project.uid)

    agg.assert_called_once_with(fake_sources, "NLP")


def test_writes_aggregated_data_to_db():
    project = _make_project_mock()
    nodes = {("PER", "lula"): {"label": "PER", "text_norm": "lula",
                                "text_display": "Lula", "mention_count": 1}}
    mentions = [{
        "key": ("PER", "lula"), "sentence_idx": 0,
        "sentence_text": "Lula falou.", "surface_text": "Lula",
        "origin_kind": "page", "origin_uid": "pg-1",
    }]
    edges = {}

    with patch("app.services.knowledge_pipeline._load_project", return_value=project), \
         patch("app.services.knowledge_pipeline._delete_existing"), \
         patch("app.services.knowledge_pipeline._iter_sources", return_value=[]), \
         patch("app.services.knowledge_pipeline.get_nlp"), \
         patch("app.services.knowledge_pipeline.aggregate_sources",
               return_value=(nodes, mentions, edges)), \
         patch("app.services.knowledge_pipeline._write_graph") as write:
        rebuild_project_knowledge(project.uid)

    write.assert_called_once_with(project, nodes, mentions, edges)


def test_sets_status_processing_before_work():
    project = _make_project_mock()
    seen_status = []

    def capture_status(*args, **kwargs):
        seen_status.append(project.knowledge_status)

    with patch("app.services.knowledge_pipeline._load_project", return_value=project), \
         patch("app.services.knowledge_pipeline._delete_existing", side_effect=capture_status), \
         patch("app.services.knowledge_pipeline._iter_sources", return_value=[]), \
         patch("app.services.knowledge_pipeline.get_nlp"), \
         patch("app.services.knowledge_pipeline.aggregate_sources",
               return_value=({}, [], {})), \
         patch("app.services.knowledge_pipeline._write_graph"):
        rebuild_project_knowledge(project.uid)

    assert seen_status == ["PROCESSING"]
