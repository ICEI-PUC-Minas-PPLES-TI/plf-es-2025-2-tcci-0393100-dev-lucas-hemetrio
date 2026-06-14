"""Worker de processamento em subprocesso.

Roda o pipeline pesado (OCR do PDF + rebuild do grafo) em um processo Python
separado do servidor web, para que o GIL do spaCy/renderização nunca trave as
leituras (`/stream`). Substitui o uso de FastAPI BackgroundTasks para documentos.

Uso:
    python -m app.worker document <doc_uid>     # OCR do PDF (dispara rebuild se INDEXED)
    python -m app.worker rebuild  <project_uid> # só reconstrói o grafo do projeto
"""
import logging
import subprocess
import sys
from pathlib import Path

from app.db.database import connect_to_db
from app.services.knowledge_pipeline import rebuild_project_knowledge
from app.services.ocr_pipeline import process_document

logger = logging.getLogger(__name__)

# Raiz do backend (diretório que contém o pacote `app/`), usada como cwd do subprocesso.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def spawn_worker(command: str, arg: str) -> None:
    """Dispara o worker em um processo separado e retorna imediatamente.

    Não espera o término. `start_new_session=True` desacopla o worker do grupo de
    processos do Uvicorn, então um `--reload` não mata um job em andamento.
    Propaga exceção se o processo não conseguir iniciar — o chamador decide o que
    fazer (ex.: marcar o documento como FAILED).
    """
    subprocess.Popen(
        [sys.executable, "-m", "app.worker", command, arg],
        cwd=str(_BACKEND_ROOT),
        start_new_session=True,
    )


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO)

    if len(argv) != 2:
        logger.error("uso: python -m app.worker <document|rebuild> <uid>")
        return 2

    command, arg = argv

    if command not in ("document", "rebuild"):
        logger.error("comando desconhecido: %s", command)
        return 2

    # Subprocesso novo: abre a conexão Neo4j antes do pipeline, senão o neomodel
    # usaria o DATABASE_URL default e falharia com AuthError.
    connect_to_db()

    if command == "document":
        process_document(arg)
    else:
        rebuild_project_knowledge(arg)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
