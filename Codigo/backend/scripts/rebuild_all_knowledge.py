"""Dispara rebuild_project_knowledge para todos os projetos do banco.

Útil para validar o pipeline NER+RE contra dados reais sem precisar reprocessar
o OCR (que já está INDEXED). Idempotente: apaga grafo do projeto e recria.

Uso:
    cd backend && source venv/bin/activate && python scripts/rebuild_all_knowledge.py
"""
import logging
import sys
import time

# Permite rodar de qualquer CWD dentro do backend
sys.path.insert(0, ".")

from app.db.database import connect_to_db
from app.models.project import Project
from app.services.knowledge_pipeline import rebuild_project_knowledge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("rebuild_all")


def main():
    connect_to_db()
    projects = list(Project.nodes.all())
    log.info("Found %d projects", len(projects))

    summary = []
    for i, project in enumerate(projects, 1):
        log.info("[%d/%d] Rebuilding project uid=%s name=%r",
                 i, len(projects), project.uid, project.name)
        t0 = time.time()
        try:
            rebuild_project_knowledge(project.uid)
            project.refresh()
            dt = time.time() - t0
            log.info("  → status=%s (%.1fs)", project.knowledge_status, dt)
            summary.append((project.uid, project.name, project.knowledge_status, dt))
        except Exception as exc:
            log.exception("  → FAILED externally: %s", exc)
            summary.append((project.uid, project.name, f"CRASH: {exc}", time.time() - t0))

    print("\n=== Summary ===")
    for uid, name, status, dt in summary:
        print(f"  {status:12s} {dt:5.1f}s  {uid}  {name!r}")


if __name__ == "__main__":
    main()
