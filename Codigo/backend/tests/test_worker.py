"""Testes do worker em subprocesso (app/worker.py).

O worker é só o roteador entre a linha de comando e o pipeline já testado; os
pipelines em si são mockados. Garante que cada comando chama a função certa e que
entradas inválidas não viram exceção silenciosa.
"""
from unittest.mock import patch

from app import worker


def test_document_command_runs_ocr_pipeline():
    with patch("app.worker.connect_to_db"), patch(
        "app.worker.process_document"
    ) as mock_proc, patch(
        "app.worker.rebuild_project_knowledge"
    ) as mock_rebuild:
        rc = worker.main(["document", "doc-1"])

    assert rc == 0
    mock_proc.assert_called_once_with("doc-1")
    mock_rebuild.assert_not_called()


def test_rebuild_command_rebuilds_graph():
    with patch("app.worker.connect_to_db"), patch(
        "app.worker.process_document"
    ) as mock_proc, patch(
        "app.worker.rebuild_project_knowledge"
    ) as mock_rebuild:
        rc = worker.main(["rebuild", "proj-1"])

    assert rc == 0
    mock_rebuild.assert_called_once_with("proj-1")
    mock_proc.assert_not_called()


def test_main_connects_to_db_before_running_pipeline():
    # O worker roda em subprocesso novo: precisa abrir a conexão Neo4j ANTES do
    # pipeline, senão o neomodel cai no DATABASE_URL default e dá AuthError.
    order = []
    with patch(
        "app.worker.connect_to_db", create=True,
        side_effect=lambda: order.append("connect"),
    ), patch(
        "app.worker.rebuild_project_knowledge",
        side_effect=lambda uid: order.append("rebuild"),
    ), patch("app.worker.process_document"):
        rc = worker.main(["rebuild", "proj-1"])

    assert rc == 0
    assert order == ["connect", "rebuild"]


def test_unknown_command_returns_error_code():
    with patch("app.worker.process_document") as mock_proc, patch(
        "app.worker.rebuild_project_knowledge"
    ) as mock_rebuild:
        rc = worker.main(["bogus", "x"])

    assert rc == 2
    mock_proc.assert_not_called()
    mock_rebuild.assert_not_called()


def test_wrong_arg_count_returns_error_code():
    assert worker.main(["document"]) == 2


def test_spawn_worker_invokes_subprocess():
    with patch("app.worker.subprocess.Popen") as mock_popen:
        worker.spawn_worker("document", "doc-1")

    args, kwargs = mock_popen.call_args
    cmd = args[0]
    assert cmd[1:] == ["-m", "app.worker", "document", "doc-1"]
    assert kwargs["start_new_session"] is True
